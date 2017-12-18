Jane's Dream
============

Introduction
------------
Jane has job as a part-time postwoman. She uses the job to visit
new places as part of her route, sometimes making detours. "She wants
to automate the whole process". Based on the context in the paragraph
I take this to mean that she wants the route selection to be automated.

This means that she has a few mandatory addresses that she must visit
to deliver the letters in her care. Besides that she can select a few 
extra destinations that she wants to visit during her round. The system
is to calculate an optimal route for her.

Exploration of the problem
--------------------------
In order to understand the problem a bit more, I interviewed a friend from
my chess club who works for TPG. He explained to me that Jane would probably
be bored quite quickly, since a typical postal area is around 30 streets. 
Postal delivery will be ca 500 letters or other mail items. The routing problem
is also special, since postmen sort their letters for odd and even numbers, so
they can walk one side of the street going up and the other side going down. 

Possible approaches
-------------------
At first, I thought the problem resembled the travelling salesmen problem (TSP). 
The addresses of the mail (zip codes + street numbers) can map to vertices.
Assuming we can find a (shortest) distance function between vertices (and that
triangular inequality holds) we can use the distance function to generate a matrix
of edges between vertices. This way, the problem is reduced to the travelling 
salesman.

The TSP is NP-hard, but the problem size here is fairly small. With an order
of magnitude brute force is infeasible without some serious hardware, but there
are quite good heuristical algorithms. In the past I implemented a 2-OPT 
algorithm for TSP as part of a course in discrete optimization.

However, after speaking to my friend, I noted some anomalies compared to the 
travelling salesman. For one, mail men typically do not often cross the street 
when walking their route, but first do one side of the streen and then another.

Also postmen do not really travel from address to address. Instead, they go from 
street to street. With the provision noted earlier, that also means that when
postman finishes as street, they are back where they started. (Which is a good
thing, as otherwise they would have to get back for their bike).

I then mentally toyed with variations of the TSP. One option I considered:
1. instead of modelling the individual addresses as vertices, model the
two end-points of the streets as vertices. Then select the group of end-points
such that each street has at least one end-point selected and the end-points 
have the minimum average distance from each other.

However, intuitively, this looked like the wrong approach. I googled a bit on
arc routing problems. With this I hit the Chinese Postman Problem (CSP), which 
seemed a lot more suitable. The Chinese Problem finds an optimal route for
traversing all edges in a graph. If we model the streets in our postal area
as edges, we have reduced Jane's problem to the CSP.

The Chinese Postman Problem can be solved in polynomial time. 

The only difference between CSP and Jane's problem is that in Jane's case not all
edges have to be traversed. In the Wikipedia article they note this as a
variant. "Minimize the 'Rural Postman Problem': solve the problem with some 
edges not required." Unfortunately, the article pointing to that problem
is not (freely) accessible via the internet. With a bit of google, I found
this article: [Arc Routing Problems, Part II: The Rural Postman Problem](https://pubsonline.informs.org/doi/pdf/10.1287/opre.43.3.399).

This seems most promising, so continue with that.

The Rural Postman Problem
-------------------------
So perhaps Jane's problem is more like a Rural Postman Problem (RPP), which
makes sense considering the earlier description of the problem.

The RPP comes in two varieties, directed and undirected. These map to the
varieties in which a postman crosses the roads while delivering the mail on
that road or walks the road up and down. In the first case each road
maps to an (undirected) edge. In the second case each road maps to two
(directed) edges.

Practical Considerations
------------------------
We need a way to import maps. I have no experience doing anything related to 
maps. After some browsing I came up with OpenStreetMap (OSM) and PostGIS.
I imported a small map from OSM (the area around my house, so I can easily
check it for correctness). After some hacking, I managed to map postal codes
to line segments. See `postgid.md` for more of my efforts.

At this stage, we can think of input and output formats and (API) user 
experience. We want Jane to input a number of addresses where she has to
deliver the mail. She can then add a number of extra addresses she wants
to visit.

The algorith described in the article above seems implementable,
but I am sure other people will have had a stab at it. 
See [Andrew Brooks library](https://github.com/brooksandrew/postman_problems).

Unfortunatly, the algorithm used only works when the graphs of required edges is
connected. This limitation does not hold for us. In "Arc Routing Problems",
we see a few algorithms that may work. I started implememnting those in 
`solver.py`, but the work is far from finished.


