# MapZen Exporter

> Service used to convert and export Admin boundaries such as MapZen Borders
> into [POSM Extracts](https://github.com/nyaruka/posm-extracts) expected format.

### Setup Guide

You need to do the following:

```sh
    $ git clone https://github.com/ehealthafrica/mapzen-exporter && cd mapzen-exporter

    $ virtualenv mapzen_env

    $ source mapzen_env/bin/activate

    $ pip install -r pip-required.txt

    $ cd exporter

    $ cp settings.yaml.temp settings.yaml
```

### Usage
- In settings.yaml set the following:
    - `data_dir` : full path to the input geojson files directory
    - `output_dir`: full path to output directory
    - `mapzen_file_url`: url to online archived file that holds each country's admin boundaries files
    - `geojson_dir_name`: the path to directory that contains extracted admin boundaries geojson files
    - admin_levels:
      > `- 2` # Default is 2 for all countries

      > `- 4` # OSM Admin level for next sub region for a given country e.g 4 for Nigerian States

      > `- 6` # OSM Admin level for next lower admin level for a given country e.g 6 for Nigerian LGAs

      > `- 8` #OSM Admin level for next lower admin level for a given country e.g 8 for Nigerian Wards

- To run, while in exporter directory

```sh
    $ python exproter.py
 ```