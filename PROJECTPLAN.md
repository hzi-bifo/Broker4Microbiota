
# TODO

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