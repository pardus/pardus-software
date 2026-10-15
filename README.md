# Pardus Software Center

Pardus Software Center is a software center front-end for debian based operating systems.

It is currently a work in progress. Maintenance is done by <a href="https://www.pardus.org.tr/">Pardus</a> team.

You can see the web interface of the application center at <a href="https://apps.pardus.org.tr/">Pardus Apps</a>.

[![Packaging status](https://repology.org/badge/vertical-allrepos/pardus-software.svg)](https://repology.org/project/pardus-software/versions)

### **Dependencies**

This application is developed based on Python3 and GTK+ 3. Dependencies:
```bash
gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-soup-2.4 gir1.2-vte-2.91 gvfs gvfs-backends python3-apt python3-cairo python3-distro python3-netifaces python3-psutil
```

### **Run Application from Source**

Install dependencies
```bash
sudo apt install gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-soup-2.4 gir1.2-vte-2.91 gvfs gvfs-backends python3-apt python3-cairo python3-distro python3-netifaces python3-psutil
```
Clone the repository
```bash
git clone https://github.com/pardus/pardus-software.git ~/pardus-software
```
Run application
```bash
python3 ~/pardus-software/src/Main.py
```

### **Run GTK regression checks**

With the application dependencies installed, run from a desktop session:

```bash
python3 tests/offline_navigation.py
```

For a headless session, install `xvfb` and `xauth` and run
`xvfb-run -a python3 tests/offline_navigation.py`.
These checks load the real Glade widgets and test offline navigation and search
with supplied connection/permission/APT states. They do not start network or
package workers, modify packages, or replace a full application test.
They are run explicitly, outside the Debian package build.

### **Build deb package**

```bash
sudo apt install devscripts git-buildpackage
sudo mk-build-deps -ir
gbp buildpackage --git-export-dir=/tmp/build/pardus-software -us -uc
```

### **Screenshots**

![Pardus Software Center 1](screenshots/pardus-software-1.png)

![Pardus Software Center 2](screenshots/pardus-software-2.png)

![Pardus Software Center 3](screenshots/pardus-software-3.png)

![Pardus Software Center 4](screenshots/pardus-software-4.png)

![Pardus Software Center 5](screenshots/pardus-software-5.png)

![Pardus Software Center 6](screenshots/pardus-software-6.png)

![Pardus Software Center 7](screenshots/pardus-software-7.png)
