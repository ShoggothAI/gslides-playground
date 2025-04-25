# gslides-playground

The general review of the Google Slides API is at https://developers.google.com/workspace/slides/api/guides/overview

This repo contains Pydantic domain objects matching the JSON that the google slides API returns.

It also contains methods to create Google Slide objects back from these domain objects. 
The set of methods is unfortunately incomplete as the Google Slides REST API's structure
is only partially aligned to the structure of the JSON returned by the API.