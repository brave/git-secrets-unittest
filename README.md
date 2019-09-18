# Tesing git-secrets

This `unittest-git-secrets.py` script can easily validate both git-secrets and git pre-commit
hook functions correctly.

This is intended to be cross platform, so it should work on Mac and Linux
without any modification.

NOTE: On Windows, this script works in WSL, but not on Powershell. This is
because `git-secrets` is a bash script, and bash cannot run in Powershell. In
order to use this script and `git-secrets` it must be run in WSL.

## Prereqs

You must have the following prereqs configured:

* Python 3.4 or above
* The tool [git-secrets](https://github.com/awslabs/git-secrets) must be
  installed and configured to recognize AWS patterns
* You must setup a Git pre-commit hook:
  * Use the Git config variable
    ['core.hooksPath'](https://github.com/awslabs/git-secrets#advanced-configuration)(preferred),
    or the Git config variable
    ['init.templateDir'](https://git-scm.com/docs/git-init#_template_directory).

## Running the Test

To execute the test script, run the command:

```python3 unittest-git-secrets.py```

### Successful output

```
$ python3 unittest-git-secrets.py
Command 'git commit -m 'test pre-commit hook'' return code: 1
Command output:
 test.txt:1:aws_secret_access_key = NOTAVALIDSECRETACCESSKEY

[ERROR] Matched one or more prohibited patterns

Possible mitigations:
- Mark false positives as allowed using: git config --add secrets.allowed ...
- Mark false positives as allowed by adding regular expressions to .gitallowed at repository's root directory
- List your configured patterns: git config --get-all secrets.patterns
- List your configured allowed patterns: git config --get-all secrets.allowed
- List your configured allowed patterns in .gitallowed at repository's root directory
- Use --no-verify if this is a one-time false positive

.
----------------------------------------------------------------------
Ran 1 test in 0.116s

OK
```

We use the Python Unittest framework, so the output will look like a unit test.
It should show `OK` on the last line, as above. It will have the string `[ERROR]
Matched one or more prohibited patterns`, which means that `git-secrets`
succesfully found a prohibited pattern, a scenario that we intentionally create
within the script by creating a temporary Git repository. This output means that
`git-secrets` worked as expected and you are ready to safely commit to GitHub
repositories.

### Unsuccessful output

If the script does not work correctly, it will show output similar to below. It
will say that the test failed. This could mean that your git hook is not setup
properly, or `git-secrets` is not installed properly, or the script itself had
an error.

```
F
======================================================================
FAIL: test_git_pre_commit_hook (__main__.Test_01_GitPreCommitHook)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "unittest-git-secrets.py", line 175, in test_git_pre_commit_hook
    self.assertTrue(self.g1.trigger_hook(self.outfile))
AssertionError: False is not true

----------------------------------------------------------------------
Ran 1 test in 0.146s

FAILED (failures=1)
```

If this occurs, please re-read the steps for installing both `git-secrets`, and
your git hooks in the [prereqs](#prereqs) section above to verify you have
configured your environment properly.

## Meta

Author: [Matt Bacchi](mailto:mbacchi@brave.com)

Distributed under the Mozilla Public License, v. 2.0. See ``LICENSE`` or
http://mozilla.org/MPL/2.0/ for more information.

## Contributing

1. Create your branch (`git checkout -b fooBar`)
2. Commit your changes (`git commit -am 'Add some fooBar'`)
3. Push to the branch (`git push origin fooBar`)
4. Create a new Pull Request
