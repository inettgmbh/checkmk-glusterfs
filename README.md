# CheckMK GlusterFS Monitoring Plugin

## Description

Small Monitoring Plugin for GlusterFS, tested on GlusterFS 11.0 and CheckMK 2.1.0p24

Included Checks:
 - Peer Status
 - Volume Info:
   - general info
   - heal info
   - split-brain info
   - rebalance status
 
Added to CheckMK:
- Host Labels to identify Gluster Servers
- One Service for each Peer in CheckMK
- One Service for each Volume in CheckMK

## Installation
The mkp archive can be downloaded directly from the [release](https://github.com/inettgmbh/checkmk-glusterfs/releases/latest) section
and installed by following the [official checkmk documentation](https://docs.checkmk.com/latest/en/mkps.html).
