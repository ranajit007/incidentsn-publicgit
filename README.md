# incidentsn
Incident analyzer Nestlé


## Setup process

* Install docker from: https://www.docker.com/

* Enable HYPER V on windows: https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/quick-start/enable-hyper-v#enable-the-hyper-v-role-through-settings

* Suggestion: Increase page size to 16 GB on host OS

## Configuration process

Inside the config collection you may configure the following settings:
* key=selenium_config: This key contians the credetentials to be used by the Webscrapper.
* type=prediction_config: This collections setups what predictions should be executed on the Get prediction button

To import settings and data, place into the following path all .json files, where the filename will be the collection:
```bash
/seed/files/
```
Example:
```bash
    Directory: C:\[...]\incidentsn\seed\files


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----         10/7/2020  12:55 PM            950 config.json
-a----         10/7/2020   1:30 PM       53455635 incidents_ewm_full.json
-a----         10/7/2020  12:55 PM           3880 ProposedProcedure.json
```
## Usage

* Startup docker daemon and run interactive:
```bash
docker-compose up
```
* Startup docker daemon and run background:
```bash
docker-compose up -d
```
* For forcing create:
```bash
docker-compose up --build
```

* Open your web browser using the specified URL:
```bash
http://127.0.0.1:5000/
 ```
 * User interface should be available
