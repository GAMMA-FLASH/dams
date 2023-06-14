GammaFlash client/server tools.

GF Client is aimed at receiving data from each DAM and save the waveforms in HDF5 format (DL0).
Instead, the GF Server could be used to playback already existing DL0 data for testing/debug purposes.

Usage:

1. Launch the server

python gfse.py --addr 172.17.0.2 --port 1234 --indir /mnt/DL0 --rpid 1

2. When the server is running launch the client

python gfcl.py --addr 172.17.0.2 --port 1234  --outdir ./test --wformno 10
