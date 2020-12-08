=========================================
EPR: Electron Paramagnetic Resonance
=========================================

The EPR *project* provides the measurement software for the EPR lab course as conducted at the University of Stuttgart, Germany.

#ToDo
-----
- implement a magnetic field sweep
- simulate the experiment with dummy hardware first
- implement a Nidaq measurement card - code is there needs to be adopted
- read out the magnetic field using hall sensor output voltage
- use the hall sensor readout to set the static magnetic field B0
- use the readout to stabilize and perform the magnetic field sweep

#Install
--------
1. get [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. conda env create -f conda_epr.yml
3. install Microsoft Visual C++ 14.0 or greater (https://visualstudio.microsoft.com/de/visual-cpp-build-tools/)
4. pip install pillow, nidaqmx, fonttools, enable, chaco

#Run
----
1. open conda shell
2. source activate epr
3. ipython
4. run epr.py
