## Title

[OC] I mapped where 7,300 novels are set. London (549), New York (510) and Paris (422) dominate; Mumbai, a city of 19 million, has 4

## Body

Wikidata records the real narrative locations of thousands of books, so I put every literary work with a mapped setting on one map: 13,218 works, 7,300 of them novels, in 4,057 places. Three cities appear in 20% of the novels. Paris led in the age of Balzac (44% of mapped novels published 1830 to 1849), New York from 1950 to 1989, London since 1990. Authors mostly stay home: the median distance from an author's birthplace to the setting is 343 km. Europe has 10% of the world's people and 54% of the novels; Asia 60% and 9%. Big caveat, and part of the story: this maps what volunteers have catalogued. Denmark alone has 476 setting places, more than China and India together (110), thanks to a very thorough Danish effort, and Pittsburgh ranks eighth in the world. Interactive map with search by book or author, genre and period filters, and lines from each author's birthplace: https://maps.tristanhotham.com/novel-settings/

## Source comment

Source: Wikidata (CC0), narrative location (P840) with coordinates for every literary work, plus authors' birthplaces (P19), publication dates, genres and forms, queried with QLever. Novel = form novel or novella, or a class named novel. City areas merge places within 25 km of a city of 250,000+. Outlines and populations: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: https://maps.tristanhotham.com/novel-settings/
Paper: https://doi.org/10.5281/zenodo.23872997
Blog post: https://blog.tristanhotham.com/2026/10/31/novel-settings/
