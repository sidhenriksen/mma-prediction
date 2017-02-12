# mma-prediction
This is a repository for pulling data about MMA fights from the web
and generating fight predictions based on said data. 

## Usage:
First, clone the repository.
### Building the database
Navigate to the repository directory, and execute 

	python fmcrawler_sql.py
	
This will crawl the Fightmetric website. Crawling is kept at an artificially
slow rate since a high crawl rate puts a lot of stress on the host and
generally results in a ban. Thus, crawling the page exhaustively and
conscientiously will take some time (but less than 30 mins).

Note: various common Python libraries are necessary in order for the
code to run successfully. 

### Exploring the data (optional)
Import fmprocess, and call

	import fmprocess
    fighters = fmprocess.get_fighters()
	
This will return a dictionary with all fighters on the Fightmetric website.
To get a given fighter's fights, we do

	fights = fmprocess.get_fights('Conor McGregor')
	
This will return all of the fights featuring Conor McGregor.

### Running the classifier
Simply running the script classifier.py will generate some informative
printouts about classifier performance and feature importances.
To train the classifier, run:

	import classifier
	myClassifier = classifier.build_classifier()
	
And now we can do interesting things, like make it predict the outcome of matchups
it has never seen before. For example:

	classifier.predict_fight(myClassifier,'Conor McGregor','Nick Diaz')
	
Note that this has to be interpreted with some caution, particularly when you're
dealing with cases that the classifier does not see very often. For example,
Demetrious Johnson's (Flyweight champion) features (e.g. number of wins)
overcompensates for his small size compared to a larger opponent (e.g.
Conor McGregor, who is several weight classes above). The problem is that these
examples are very rarely seen, and so the model has no way of knowing how this
would play out.

Nevertheless, it is fun to play around with, and potentially predictive above and
beyond the odds provided by bookies. 


## Project structure
The project is split into four components:
### The API
The API (fightmetric.py) gives a series of functions which easily handles pulling
data from the web pages. There should be no need to interact with
this as all the relevant data gets pulled.

### The crawler
The crawler (fmcrawler_sql.py) uses the API to crawl the entire Fightmetric.com site.
It takes this data and puts it into an SQLite database.

### Data processing and preparation
Some data processing and prep is necessary in order to build feature vectors
for classification (fmprocess.py).

### Classifier
The classifier is a simple logistic regression model which predicts the
outcome of fights which the classifier has not been trained on. Validation is
on-going using both logistic regression and random forest classifiers. 

