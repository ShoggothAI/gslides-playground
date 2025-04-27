# gslides-playground

The general review of the Google Slides API is at https://developers.google.com/workspace/slides/api/guides/overview

This repo contains Pydantic domain objects matching the JSON that the google slides API returns.

It also contains methods to create Google Slide objects back from these domain objects. 
The set of methods is unfortunately incomplete as the Google Slides REST API's structure
is only partially aligned to the structure of the JSON returned by the API.

Example of running it to first get complete data from a presentation as a domain object,
then use that object to (almost successfully, so far :) ) clone a slide in it, is in
`playground/replace.py`. 

Instructions on how to create the right `credentials.json` are in [CREDENTIALS.md](CREDENTIALS.md)

## Other Google Slides-related libraries, both Python and TS:
https://github.com/daattali/gslides-betternotes-extension 
The slide previews in the Speaker Notes window of Google Slides are tiny and unreadable. This extension fixes this in two ways: the slides are automatically enlarged when the Speaker Notes window is resized, and you can also drag the sidebar to manually select the perfect slides size.

https://github.com/ShoggothAI/md2googleslides Typescript, create slides from markdown (this fork fixes auth and changes the online destination of local images, 
both breaking bugs in the original).

https://github.com/michael-gracie/gslides Python, Focuses on creating new slides with charts and tables

https://github.com/vilmacio/gslides-maker Generate Google Slides from Wikipedia content.
The presentation content is adaptable to all kinds of Google Presentation Themes available.
This beta version does not yet produce slides containing images. It only produces text content.