library(tidyverse)
library(httr)

c_code <- GET("http://api.travelpayouts.com/data/en/countries.json")
c_code_resp <- jsonlite::fromJSON(rawToChar(c_code$content))
country_code_america <- c_code_resp %>%
  select(code:name) %>%
  filter(name %in% c("United States", "Mexico", "Canada", "Guatemala", "Haiti",
                     "Cuba", "Dominican Republic", "Honduras", "Nicaragua", "El Salvador",
                     "Costa Rica", "Panama", "Jamaica", "Puerto Rico", "Belize",
                     "Trinidad and Tobago", "Guadeloupe", "Bahamas", "Martinique", "Aruba",
                     "Barbados", "Saint Lucia", "Curaçao", "Grenada", "Dominica",
                     "Saint Vincent and the Grenadines", "Saint Kitts and Nevis",
                     "Antigua and Barbuda", "Cayman Islands", "Bermuda",
                     "Greenland", "Sint Maarten", "Turks and Caicos Islands", "Saint Martin",
                     "British Virgin Islands", "Caribbean Netherlands", "Anguilla",
                     "Saint Barthélemy", "Saint Pierre and Miquelon", "Montserrat"))


from <- tibble(from_code = country_code_america$code,
               from_country = country_code_america$name)
to <- tibble(to_code = country_code_america$code,
             to_country = country_code_america$name)
north_america_routes <- expand.grid(from$from_code, to$to_code)
north_america_routes <- north_america_routes %>%
  rename(from_code = Var1,
         to_code = Var2)

NA_df <- inner_join(north_america_routes, from, by = "from_code")  
NA_df <- inner_join(NA_df, to, by = "to_code")
headers <- c('accept' = 'application/json', 
             'apikey' = Sys.getenv("kiwi_key"))
api_call_vital <- function(url) {
  query <- GET(url, add_headers(.headers=headers))
  resp <- jsonlite::fromJSON(rawToChar(query$content))
  resp_df <- resp$data
  tibble(flyFrom = resp_df$flyFrom,
         flyTo = resp_df$flyTo,
         cityFrom = resp_df$cityFrom,
         cityTo = resp_df$cityTo,
         countryFrom = resp_df$countryFrom$name,
         countryTo = resp_df$countryTo$name,
         distance = resp_df$distance,
         durationDepatrure = resp_df$duration$departure,
         durationReturn = resp_df$duration$return,
         price_EUR = resp_df$conversion$EUR,
         airlines = resp_df$airlines,
         UTCarrival = resp_df$utc_arrival,
         UTCdeparture = resp_df$utc_departure,
         bookLink = resp_df$deep_link)
}

# Plane
links_plane <- paste0("https://api.tequila.kiwi.com/v2/search?fly_from=", NA_df$from_code, 
                      "&fly_to=", NA_df$to_code, 
                      "&date_from=15%2F07%2F2023&date_to=30%2F12%2F2023&curr=EUR&vehicle_type=aircraft&limit=1000") 
dataset_of_flights <- tibble()
for (i in 1:length(links_plane)) {
  data <- api_call_vital(links_plane[i])
  Sys.sleep(2.0)
  dataset_of_flights <- rbind(dataset_of_flights, data)
}


proc <- dataset_of_flights %>%
  group_by(cityFrom, cityTo) %>%
  slice(which.min(price_EUR))
write_csv(proc, "kiwi_north_america_countries_filghts.csv")

# Other vehicles
links_bus <- paste0("https://api.tequila.kiwi.com/v2/search?fly_from=", NA_df$from_code, 
                    "&fly_to=", NA_df$to_code, 
                    "&date_from=15%2F07%2F2023&date_to=30%2F12%2F2023&curr=EUR&vehicle_type=bus&limit=1000") 
dataset_of_bus <- tibble()
for (i in 1:length(links_bus)) {
  data <- api_call_vital(links_bus[i])
  Sys.sleep(2.0)
  dataset_of_bus <- rbind(dataset_of_bus, data)
}

proc <- dataset_of_bus %>%
  group_by(cityFrom, cityTo) %>%
  slice(which.min(price_EUR))
write_csv(proc, "kiwi_north_america_countries_bus.csv")


links_train <- paste0("https://api.tequila.kiwi.com/v2/search?fly_from=", NA_df$from_code, 
                      "&fly_to=", NA_df$to_code, 
                      "&date_from=15%2F07%2F2023&date_to=30%2F12%2F2023&curr=EUR&vehicle_type=train&limit=1000") 
dataset_of_train <- tibble()
for (i in 1:length(links_train)) {
  data <- api_call_vital(links_train[i])
  Sys.sleep(2.0)
  dataset_of_train <- rbind(dataset_of_train, data)
}

proc <- dataset_of_train %>%
  group_by(cityFrom, cityTo) %>%
  slice(which.min(price_EUR))
write_csv(proc, "kiwi_north_america_countries_train.csv")
