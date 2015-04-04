###########################################################################
#                                                                         #
#  Hyde Park Yelp-reviewed restaurants                                    #
#  Data cleaning                                                          #
#  Coded by Scarlett Swerdlow                                             #
#  scarlett.swerdlow@gmail.com                                            #
#  March 28, 2015                                                         #
#                                                                         #
###########################################################################

library(reshape)

#########################
#  AUXILIARY FUNCTIONS  #
#########################

aggregateByTract <- function(df) {
  
  tract <- c()
  count <- c()
  rating1 <- c()
  rating1.5 <- c()
  rating2 <- c()
  rating2.5 <- c()
  rating3 <- c()
  rating3.5 <- c()
  rating4 <- c()
  rating4.5 <- c()
  rating5 <- c()
  
  for (t in unique(df$tract)) {
    d <- df[df$tract == t,]
    c <- length(d$business.id)
    r1 <- length(d$business.id[d$rating == 1])
    r1.5 <- length(d$business.id[d$rating == 1.5])
    r2 <- length(d$business.id[d$rating == 2])
    r2.5 <- length(d$business.id[d$rating == 2.5])
    r3 <- length(d$business.id[d$rating == 3])
    r3.5 <- length(d$business.id[d$rating == 3.5])
    r4 <- length(d$business.id[d$rating == 4])
    r4.5 <- length(d$business.id[d$rating == 4.5])
    r5 <- length(d$business.id[d$rating == 5])
    
    tract <- append(tract, t)
    count <- append(count, c)
    rating1 <- append(rating1, r1)
    rating1.5 <- append(rating1.5, r1.5)
    rating2 <- append(rating2, r2)
    rating2.5 <- append(rating2.5, r2.5)
    rating3 <- append(rating3, r3)
    rating3.5 <- append(rating3.5, r3.5)
    rating4 <- append(rating4, r4)
    rating4.5 <- append(rating4.5, r4.5)
    rating5 <- append(rating5, r5)
  }
  
  tract.data <- data.frame(tract, count, rating1, rating1.5, rating2,
                           rating2.5, rating3, rating3.5, rating4,
                           rating4.5, rating5)
  
  return(tract.data)
}

aggregateByCA <- function(df) {
  
  comm.area <- c()
  comm.area.name <- c()
  count <- c()
  pop <- c()
  rating1 <- c()
  rating1.5 <- c()
  rating2 <- c()
  rating2.5 <- c()
  rating3 <- c()
  rating3.5 <- c()
  rating4 <- c()
  rating4.5 <- c()
  rating5 <- c()
  
  for (ca in unique(df$comm.area)) {
    d <- df[df$comm.area == ca,]
    n <- as.character(d$comm.area.name[1])
    c <- sum(d$count)
    p <- sum(d$pop)
    r1 <- sum(d$rating1)
    r1.5 <- sum(d$rating1.5)
    r2 <- sum(d$rating2)
    r2.5 <- sum(d$rating2.5)
    r3 <- sum(d$rating3)
    r3.5 <- sum(d$rating3.5)
    r4 <- sum(d$rating4)
    r4.5 <- sum(d$rating4.5)
    r5 <- sum(d$rating5)
    
    comm.area <- append(comm.area, ca)
    comm.area.name <- append(comm.area.name, n)
    count <- append(count, c)
    pop <- append(pop, p)
    rating1 <- append(rating1, r1)
    rating1.5 <- append(rating1.5, r1.5)
    rating2 <- append(rating2, r2)
    rating2.5 <- append(rating2.5, r2.5)
    rating3 <- append(rating3, r3)
    rating3.5 <- append(rating3.5, r3.5)
    rating4 <- append(rating4, r4)
    rating4.5 <- append(rating4.5, r4.5)
    rating5 <- append(rating5, r5)
  }
  
  comm.area.data <- data.frame(comm.area, comm.area.name, count, pop, rating1, 
                               rating1.5, rating2, rating2.5, rating3,
                               rating3.5, rating4,rating4.5, rating5)
  
  comm.area.data$rating <- ((1*comm.area.data$rating1) + 
                              (1.5*comm.area.data$rating1.5) +
                              (2*comm.area.data$rating2) +
                              (2.5*comm.area.data$rating2.5) +
                              (3*comm.area.data$rating3) +
                              (3.5*comm.area.data$rating3.5) +
                              (4*comm.area.data$rating4) +
                              (4.5*comm.area.data$rating4.5) +
                              (5*comm.area.data$rating5))/rowSums(
                                comm.area.data[c(5:13)])
  
  return(comm.area.data)
}


#########################
#  READ IN, CLEAN DATA  #
#########################

# Set to correct location
data <- read.csv('~/Projects/yelp/ChicagoRestaurantsDetailed.csv', header=F)
data <- rename(data, c(V1 = 'business.id', V2 = 'business.name',
                       V3 = 'review.count', V4 = 'rating',
                       V5 = 'address', V6 = 'city', V7 = 'state',
                       V8 = 'lat', V9 = 'lng', V10 = 'tract'))
data$rating <- as.numeric(as.character(data$rating))


########################
#  AGGREGATE BY TRACT  #
########################

tract.data <- aggregateByTract(data)

# Census tract population estimates, American Community Survey, 2008-2013
# Set to correct location
tract.pop <- read.csv('~/Projects/yelp/pop_by_tract.csv', header=T, skip=1)
tract.pop$tract <- as.numeric(
  substr(as.character(tract.pop$Id2), 6, nchar(as.character(tract.pop$Id2))))

tract.data <- merge(tract.data, tract.pop, by.x='tract', by.y='tract')
tract.data <- tract.data[c(1:11,15)]
tract.data <- rename(tract.data, c(Estimate..Total='pop'))

tract.data$count.per.capita <- ifelse(tract.data$pop == 0, 0, 
                                      round(tract.data$count*1000/tract.data$pop,0))

write.csv(tract.data, 'restaurants_by_tract.csv') # For CartoDB map


#################################
#  AGGREGATE BY COMMUNITY AREA  #
#################################

# Community area equivalency file and name file, Rob Paral & Associates
# Set to correct location
comm.area.eq <- read.csv('~/Projects/yelp/tract_to_ca.csv', header=T) # CAs
comm.area.names <- read.csv('~/Projects/yelp/ca_data.csv', header=T) # CA names
comm.area.eq$Tract <- as.numeric(substr(
  as.character(comm.area.eq$Tract), 6, nchar(as.character(comm.area.eq$Tract))))

tract.data2 <- merge(tract.data, comm.area.eq, by.x='tract', by.y='Tract')
tract.data2 <- tract.data2[c(1:13,15)]
tract.data2 <- rename(tract.data2, c('Community.Area' = 'comm.area'))

tract.data2 <- merge(tract.data2, comm.area.names, 
                     by.x='comm.area', by.y='Community_area')
tract.data2 <- tract.data2[c(1:15)]
tract.data2 <- rename(tract.data2, c('Community' = 'comm.area.name'))

comm.area.data <- aggregateByCA(tract.data2)

write.csv(comm.area.data, 'restaurants_by_ca.csv')