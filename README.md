README for MMRV Project
===========================================
> [!NOTE]
> This repository is very much **Under Contruction** and not all features are be up
> and running yet.

This project concerns the development of data download, processing and analysis tools
to track soil moisture and assess it's efficacy as a metric of ecosystem health and
resilience to change. 

The `NISAR SME2` data product is the primary observational variable in this study, 
though as analysis continues more data will be added for predictive purposes.

## Setup
We have chosen to utilize the `conda` package manager to maintain a consistent environment
with that used in development. 

`conda` can be installed using these instructions for your specific operating system: 
- [Windows](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html)
- [macOS](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html)
- [Linux](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
Or by following the instructions on the `conda` website if these are unavailable.

Once installed, our environment can be replicated by running:
```conda env create -f environment.yml```
