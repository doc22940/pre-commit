from __future__ import absolute_import
from __future__ import unicode_literals

import tarfile

from pre_commit import git
from pre_commit import make_archives
from pre_commit.util import cmd_output
from testing.util import git_commit


def test_make_archive(in_git_dir, tmpdir):
    output_dir = tmpdir.join('output').ensure_dir()
    # Add a files to the git directory
    in_git_dir.join('foo').ensure()
    cmd_output('git', 'add', '.')
    git_commit()
    # We'll use this rev
    head_rev = git.head_rev('.')
    # And check that this file doesn't exist
    in_git_dir.join('bar').ensure()
    cmd_output('git', 'add', '.')
    git_commit()

    # Do the thing
    archive_path = make_archives.make_archive(
        'foo', in_git_dir.strpath, head_rev, output_dir.strpath,
    )

    expected = output_dir.join('foo.tar.gz')
    assert archive_path == expected.strpath
    assert expected.exists()

    extract_dir = tmpdir.join('extract').ensure_dir()
    with tarfile.open(archive_path) as tf:
        
        import os
        
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tf, extract_dir.strpath)

    # Verify the contents of the tar
    assert extract_dir.join('foo').isdir()
    assert extract_dir.join('foo/foo').exists()
    assert not extract_dir.join('foo/.git').exists()
    assert not extract_dir.join('foo/bar').exists()


def test_main(tmpdir):
    make_archives.main(('--dest', tmpdir.strpath))

    for archive, _, _ in make_archives.REPOS:
        assert tmpdir.join('{}.tar.gz'.format(archive)).exists()
