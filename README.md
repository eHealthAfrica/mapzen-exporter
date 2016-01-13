# MapZen Exporter

> Service used to parse and export Admin boundaries from OSM data files such as .pbf, .05m using
> [Fences Builder](https://github.com/pelias/fences-builder)
> into [POSM Extracts](https://github.com/nyaruka/posm-extracts) similar format.

### Setup Guide

You need to do the following:

```sh
    $ git clone https://github.com/ehealthafrica/mapzen-exporter && cd mapzen-exporter

    $ npm install -g fences-builder

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
    - `data_url`: url to OSM data file server
    - `input_dir`: the path to directory that fences-builder will extract admin levels from OSM data file into.
    - country_osm_id: OSM id of the country you want to extract from the data file.
    - admin_levels:
      > `- 2` # Default is 2 for all countries

      > `- 4` # OSM Admin level for next sub region for a given country e.g 4 for Nigerian States

      > `- 6` # OSM Admin level for next lower admin level for a given country e.g 6 for Nigerian LGAs

      > `- 8` #OSM Admin level for next lower admin level for a given country e.g 8 for Nigerian Wards

- To run, while in exporter directory

```sh
    $ python exproter.py run_all
 ```

### OSM Data Sources:
  Ensure that the region selected on the map covers the country you want to extract.

  Caveat: for GeoFabrik, Country OSM data file does not extract country boundary use continent's data file.

- [GeoFabrik](http://download.geofabrik.de/africa.html)
- [BBBike](http://extract.bbbike.org/)

### Test
```sh
    $ nosetests
 ```

### Utilities

- `python exporter.py init_dir` : Initialises empty data directories.
- `python exporter.py download_OSM` : Downloads given OSM data file from remote server.
- `python exporter.py extract_admins` : Extracts OSM data file admin levels as geojson into given input directory.
- `python exporter.py generate_output` : Generates a given country's admin levels and write resulting files to output
directory
- `python exporter.py run_all`: Runs all the above task in one step.