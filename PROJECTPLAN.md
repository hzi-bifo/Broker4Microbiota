
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
- [ ] make a concept and implement that we have for each order a "stauts" information, eg.. that shouwls the user over a longer timie horizon whats happens with the order, at the beginning its like on the useer side to maark it like "ready for sequencing center", save the information in the db.. Then the sequencing center woudl do somethign (nto implement this but write a few lines in CLAUDE.md how thsi shoudl be done), so they change status to "sequenced" or something. So these fields sohlud be pre-determined and one normally following the next one. maybe present all stauts also somehow on the overview at http://127.0.0.1:8000/project/1/orders/, remember the status is per order maybe a nice way to show whats current status and what should be the next one and so on? 

