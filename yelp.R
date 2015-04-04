###########################################################################
#                                                                         #
#  Hyde Park Yelp-reviewed restaurants                                    #
#  Data analysis: Hyde Park vs city                                       #
#  Coded by Scarlett Swerdlow                                             #
#  scarlett.swerdlow@gmail.com                                            #
#  March 28, 2015                                                         #
#                                                                         #
###########################################################################

library(ggplot2)

##########
#  DATA  #
##########

source('~/Projects/yelp/yelp_data.R') # Set to correct location


##############################################
#  DIFFERENCE IN HYDE PARK AND CITY RATINGS  #
##############################################

hp.data <- commAreaDist('Hyde Park', comm.area.data) # Rating freq in Hyde Park

t.test(data$rating, hp.data) # Diff in rating means, city vs Hyde Park

medianTest(data$rating, hp.data) # Diff in rating medians, city vs Hyde Park

# Diff in distributions
o <- as.data.frame(table(hp.data))
e <- as.data.frame(table(data$rating))
o <- rbind(o, c(hp.data=factor('1.5'), Freq=0)) # No 1.5-stars in Hyde Park
chisq.test(o[,2], e[,2])

# Summary of results: Statistically significant differences in averages,
# but cannot reject that overall distributions are the same. The latter 
# result is not surprising. With only 77 Hyde Park observations, the 
# Chi-squared test lacks power.

###########
#  PLOTS  #
###########

city.hist.data <- data.frame('rating' = data$rating,
                             'source' = rep('Chicago', length(data$rating)))
hp.hist.data <- data.frame('rating' = hp.data,
                           'source' = rep('Hyde Park', length(hp.data)))
hist.data <- rbind(city.hist.data, hp.hist.data)

hst <- ggplot(hist.data, aes(x = rating)) +
  geom_histogram(binwidth = .5, origin = .75, color='white', fill='#BD0026') +
  xlab('Yelp stars') +
  ylab('Restaurants') +
  theme( text = element_text( size = 16 ) ) +
  facet_grid(source ~ ., scales = 'free')

#########################
#  AUXILIARY FUNCTIONS  #
#########################

# Creates vector of ratings for given community area
commAreaDist <- function(strCA, df) {
  d <- df[df$comm.area.name == strCA,]
  vals <- seq(1, 5, .5)
  cnts <- c(d[,5], d[,6], d[,7], d[,8], d[,9], d[,10], d[,11], d[,12], d[,13])
  rv <- rep(vals, cnts)
}

# Performs Mood's median test
# Citation: http://stats.stackexchange.com/questions/81864/
# hypothesis-test-for-difference-in-medians-among-more-than-two-samples
medianTest<-function(x,y){
  z <- c(x,y)
  g <- rep(1:2, c(length(x),length(y)))
  m <- median(z, na.rm=T)
  rv <- chisq.test(z<=m,g)
  return(rv)
}



