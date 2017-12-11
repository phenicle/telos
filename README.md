# telos
An effortless way to automate file transfer.

Telos has one job: effortless automation of file transfer. It's data-driven. Once a transfer profile has been defined, a single line is all it takes to automatically transfer a file or set of files.

You can do it with two lines, if you prefer to stretch out and relax.

Telos transfer profiles are stored in a yaml file named .telos. It lives, by default, in your home directory.

The example shows how custom variables can take advantage of auto-expanding date/time params. It also illustrates the use of splatted patterns -- patterns that contain wildcards -- to automate the transfer of multiple files.

```yaml
---
<transfer-identifier> :
 vars:
   basedir : <a-path>
   todaydate : 'YYYYMMDD'
 host: <hostname-or-ip-address>
 protocol :
   program : /usr/bin/sftp
   user: <username>
   password: <*a*s*w*r*h*d*e*>
   password_prompt: 'assword:*'
   prompt: 'sftp > '
   timeout: 15
whert :
    remote_path_pattern: '*{{ todaydate }}*'
    local_path_pattern:  '{{ basedir }}/{{ todaydate }}'
```
 
In code, the long way to transfer a file or set of files from remote to local looks like this:
 
```python
from telos import *
t = Telos(<transfer-identifier)
t.beam_me_down()
```

To transfer from local to remote, use t.beam_me_up()

You can do it in one line by passing an optional directional indicator constant to the object constructor.

```python
from telos import *
Telos(<identifier>, AUTO_BEAMUP)
```

or

```python
from telos import *
Telos(<identifier>, AUTO_BEAMDOWN)
```
