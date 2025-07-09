
# TODO

## Improvements Made (2025-07-07)

### Form Help Text Redesign
- Changed from two-column layout to inline help text below fields
- Added tooltips for additional information (e.g., checkbox help)
- More compact and follows UX best practices
- Help text is always visible and doesn't take extra horizontal space
- Added question mark icons for complex fields that show tooltips on hover

- [x] when user accesses /projects/ but there is no project, add a text description (that can be maybe changed also in the site configureaiton admin panel) that calls the user to create a new sequencing projec. This should change to a different text once there are samples, then it should be clear when the user should request a new one, or when they should edit / config the old one


-[x] The text on footer Site name is with a color thats hard to read with the background, so maybe fix it by either make it configurable the color in the admin site setting or find a other solution
- [x] http://127.0.0.1:8000/project/create/ this should look more modern/nicer. E.g. use same css / style as when doing the registration / login? also make a nice systsem that would allow to add descriptions to each field maybe these can go more to the right of the page 

Input 1
short/small description
[form]                   | longer description at the site 
                         | that woudl help the user about what is expected here

Input 2
short/small description
[form2]                  | longer description at the site 
                         | that woudl help the user about what is expected here

...

- [x] at  http://127.0.0.1:8000/project/create/  can render these input fields nicely that we add there example content that is automatically deleted when clicking on the field? e.g. for name "john doe" or whatever, with a nice effect like good pracises 
- [x] at  http://127.0.0.1:8000/project/create/  can we show which fields are required and which arent? makybe make the input boarder yellow / red/ green depending on the state? 
- [x] at  http://127.0.0.1:8000/project/create/  subbmitted checkpbox needs content, not sure, I think its "is this already submitted to ENA" 
- [x] "save" shoudl be more like "submit" right? maybe have a "clear" butten that clears all fields and shows again the example text htere 
- [x] change "Project" title to something more deteiled, also add there text that woudl guide the user what he is doing here... maybe make text and title editable in the admin site admin page 
- [ ] for development reasons, add a button "fill in example data" thw would fill in example data that looks nice

## Order form (/project/1/orders/)

- [ ] add here text that can be changed in admin site settings
- [ ] better formatting here, e.g. spacing between the 2 buttons?
- [ ] on http://127.0.0.1:8000/project/1/orders/create/, present here eveything in the same style as http://127.0.0.1:8000/project/create/, e.g. with fileld out examples with clear button and with help text and long-form help text? 
- [ ] each "order" should have a status, maybe there should be a button "mark completed" also 
- [ ] for development reasons, add a button "fill in example data" thw would fill in example data that looks nice
- [x] make a concept and implement that we have for each order a "stauts" information, eg.. that shouwls the user over a longer timie horizon whats happens with the order, at the beginning its like on the useer side to maark it like "ready for sequencing center", save the information in the db.. Then the sequencing center woudl do somethign (nto implement this but write a few lines in CLAUDE.md how thsi shoudl be done), so they change status to "sequenced" or something. So these fields sohlud be pre-determined and one normally following the next one. maybe present all stauts also somehow on the overview at http://127.0.0.1:8000/project/1/orders/, remember the status is per order maybe a nice way to show whats current status and what should be the next one and so on?


## Integration with file system
- [ ] sample should be able to be associated to reads, e.g. either a single file per sample or a set of files since it could be PE data (e.g. sample 1 is associated to `read_file1.fastq.gz` and `read_file2.fastq.gz`). The path to these reads should be stored in the the table that we already have called app_read, there is a column file 1 and file2, the full file path should be there, its associated to the sample. We have a simluation script that is generating sample entries but its not creating the files its in admin.py in create_test_reads. This is just adding path to the samples but its not creaing file, but creates read objects. 

## Project submission

- manually 

## file upload to ENA of reads only (?)


- we need a session ID that can be retrieved manually and be updated to a project
- or go to "projects" -> select project and "Generate XML and create project submission" -> this will create ad project submitssion objects, which ccreates XML files that can be send to ENA. We have a under "project submisssions" then we have "register samples to ENA" which is currently failing. 
- this should get an API response which is saved to Project submsissions, in "Recipt xml" this sould be parsed.
- this requires env varibales in .env 
- then its get a `study_accession_id"  submission ID in the response I think?

e.g. here 

CREATE TABLE IF NOT EXISTS "app_project" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(100) NULL, "alias" varchar(100) NULL, "description" text NULL, "study_accession_id" varchar(100) NULL, "alternative_accession_id" varchar(100) NULL, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "submitted" bool NOT NULL);
CREATE INDEX "app_project_user_id_d99fd018" ON "app_project" ("user_id");

this shoudl be parsed and shown in the admin panel. 

- smaple uplaod process, todo, its just the registration of a sample



## Start a MAG run from reads or set of reads

The admin should have the ability to create a MAG run for a single sample or a set of samples. Logically it should be a set of samples 
- A MAG has has a definition, which is in app_magrun, which is also referencing the reads. The idea. Mayb we can have a better user itnerface to define this run? There is also a app_magruninstance which has a ID, status and references to magrun which has location on disk where the files generated will exist. Magrun will ultimately call nextflow to create these files on disk. 

- There is a admin function that takes a mag runs definition and "Run MAG pipeline" action, this will trigger a asynchounsous job at ... it creates a mag run instance object, mag run instance object references the unqiue path, create script.sh, passed to slurm async_call.py. When the slrum job completes, its then runs an associated hook app.hooks.process_mag_results which is in hooks.py

- when jobs completed its updating mag run status depending on return code and since mag run created various things like genome binning, (created files on disk). the hook is creating objects in django wrapped around on-disk objects. e.g. for each of the reads its looking for the appropriate assembly, hooks.py, line 54, looking up assembly file on disk created by mag run and craeting an assembly object in django referencing that, thats important since we need it later for file upload. so this should be visible in the django admin panel somehow. 
- when mag workflow si run, its creating files on disk, but django is not knowling anything of that so it creataes objects. 
- assembly objects, twin objects, and alignment files as well... 
- at this point we got the mag_run object and alignment object and multiple bins... 
- [ ]the next step then is to show this in the admin panel what objects are there...


- [ ] now its about a "submit" function that should be integrated to the app. 



- [ ]  we have MAgRun oject it has a stauts, samplesheet content and cluster config... 

# SUBMG

- start a submg run for a project, Go to projecs table, admin script "Generate subMG run for this project" this  creasts sub_mg_runs which creatwes a bit Yaml file, which is a submg yaml file, its the input that submg needs

submg instance reference submg definintion, is path on disk where the acutal yaml file is created. 

when you click on a submg run definitoin and chose action run submg, it creates the ymal file fscript and kicked off, 

yaml file -> submg -> generates 