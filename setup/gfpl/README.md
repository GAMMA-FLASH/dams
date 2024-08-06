# To use GFPL

## set env vars

`DAMS` is the folder pointing to the dams repository root folder.

`ODIR` is the DL0 and DL2 output folder for the current obervation.

## create a symbolic link to a .ini file

```
ln -s </path/to/gfcl.machine.ini> $DAMS/dl0/gfcl.ini
```

## setup current time on main computer

```
date -s YYYY-MM-DD HH:mm:SS
```
example to set date and time to 6th august 2024 at 13:24:50
```
date -s 2024-08-06 13:24:50
```

## execute bootstrap2

```
cd $DAMS/setup/gfpl && ./bootstrap2.sh
```

## start the acquisition

```
cd $DAMS/setup/gfpl && ./startall.sh
```
