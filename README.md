# StudDP
StudDP is a file downloader for [Stud.IP](http://studip.de/). It uses the 
[Stud.IP: Rest.IP](http://studip.github.io/studip-rest.ip/) plugin to download files
when they changed or are not existent on the file system.

## SetUp

To set it up, do the following:

```sh
git clone https://github.com/Faedrivin/StudDP
cd StudDP
cp default_config.json config.json
```

Modify the config.json:
```json
{
    "username": "",
    "password": "",
    "base_address": "https://studip.uos.de/plugins.php/restipplugin",
    "local_path": "~/studip",
    "interval": 1200,
    "last_check": -1
}
```

* `username` is your login name.
* `password` is your password.
* `base_address` is the addres up to the root of your Rest.IP plugin. Leave out any trailing slashes.
* `local_path` is your local folder where files should be downloaded to.
* `interval` is the checking interval in seconds (so the default is 20 minutes).
* `last_check` is the last timestamp when checks were performed. Leave this as -1.

## Run

To run it use:

```sh
./StudDP.py&
```

To stop it use:

```sh
./stop.sh
```

## Other information

To view the log use:

```sh
tail -f ~/.studdp/info.log
```

To uninstall use:

```sh
rm -rf StudDP
rm -rf ~/.studdp
```

