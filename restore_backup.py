import argparse
import gzip
import hashlib
import json
import os
import tarfile
from pathlib import Path, PurePosixPath

BLOCK = 1024 * 1024

class PartReader:
    def __init__(self, paths):
        self.paths = iter(paths)
        self.file = None
    def read(self, n=-1):
        if n < 0:
            raise ValueError('Unbounded archive read is unsupported')
        result = bytearray()
        while len(result) < n:
            if self.file is None:
                try:
                    self.file = open(next(self.paths), 'rb')
                except StopIteration:
                    break
            chunk = self.file.read(n-len(result))
            if chunk:
                result.extend(chunk)
            else:
                self.file.close()
                self.file = None
        return bytes(result)
    def close(self):
        if self.file:
            self.file.close()
            self.file = None

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(BLOCK),b''):
            h.update(block)
    return h.hexdigest()

def asset(directory, spec):
    name=spec['name']
    if Path(name).name != name or name in ('.','..'):
        raise ValueError('Unsafe asset name')
    path=directory/name
    if path.stat().st_size != spec['bytes'] or digest(path) != spec['sha256']:
        raise ValueError('Asset size or SHA-256 does not match: '+name)
    print('Verified',name,flush=True)
    return path

def restore(assets, destination):
    assets=Path(assets).resolve()
    destination=Path(destination).resolve()
    summary=json.loads((assets/'summary.json').read_text(encoding='utf-8'))
    parts=[asset(assets,p) for p in summary['parts']]
    manifest_path=asset(assets,summary['manifest'])
    root=destination/'new_viral_proj'
    if root.exists():
        raise FileExistsError('Refusing to overwrite existing destination: '+str(root))
    destination.mkdir(parents=True,exist_ok=True)
    count=dirs=total=0
    reader=PartReader(parts)
    try:
        with gzip.open(manifest_path,'rt',encoding='utf-8') as manifest:
            with gzip.GzipFile(fileobj=reader,mode='rb') as zipped:
                with tarfile.open(fileobj=zipped,mode='r|') as archive:
                    for item in archive:
                        line=manifest.readline()
                        if not line:
                            raise ValueError('Archive has an extra item')
                        row=json.loads(line)
                        name=item.name.rstrip('/')
                        parts_name=PurePosixPath(name).parts
                        if name != row['path'].rstrip('/') or not parts_name or parts_name[0] != 'new_viral_proj' or any(p in ('..','.') or '\\' in p or ':' in p for p in parts_name):
                            raise ValueError('Unsafe or mismatched archive path: '+name)
                        path=destination.joinpath(*parts_name)
                        if row['type']=='directory':
                            if not item.isdir():
                                raise ValueError('Directory type mismatch: '+name)
                            path.mkdir(parents=True,exist_ok=True)
                            dirs+=1
                        else:
                            if not item.isfile() or item.size != row['size']:
                                raise ValueError('File type/size mismatch: '+name)
                            path.parent.mkdir(parents=True,exist_ok=True)
                            h=hashlib.sha256()
                            with archive.extractfile(item) as src, open(path,'xb') as dst:
                                for block in iter(lambda:src.read(BLOCK),b''):
                                    dst.write(block)
                                    h.update(block)
                            if h.hexdigest()!=row['sha256']:
                                raise ValueError('File digest mismatch: '+name)
                            os.utime(path,ns=(row['mtime_ns'],row['mtime_ns']))
                            count+=1
                            total+=row['size']
                            if count%20000==0:
                                print('Restored files:',count,flush=True)
                    if manifest.readline():
                        raise ValueError('Manifest contains an additional item')
                while zipped.read(BLOCK):
                    pass
    finally:
        reader.close()
    if (count,dirs,total)!=(summary['files'],summary['directories'],summary['source_bytes']):
        raise ValueError('Restore totals do not match the backup summary')
    print('Restore verified:',count,'files,',dirs,'directories,',total,'bytes')
    print('Restored to:',root)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Verify and restore all parts of the project backup.')
    parser.add_argument('--assets',default='.',help='Folder containing summary.json, manifest.jsonl.gz, and all archive parts')
    parser.add_argument('--destination',default='.',help='Parent directory where new_viral_proj will be created')
    args=parser.parse_args()
    restore(args.assets,args.destination)

