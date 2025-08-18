library(tidyverse)
library(httr)

c_code <- GET("http://api.travelpayouts.com/data/en/countries.json")
c_code_resp <- jsonlite::fromJSON(rawToChar(c_code$content))
country_code <- c_code_resp %>%
  select(code:name) %>%
  filter(name %in% c("Germany", "United Kingdom", "France", "Italy", "Spain",
                     "Ukraine", "Poland", "Romania", "Netherlands", "Belgium",
                     "Czech Republic", "Greece", "Portugal", "Sweden", "Hungary",
                     "Austria", "Serbia", "Switzerland", "Bulgaria", "Denmark",
                     "Finland", "Slovakia", "Norway", "Ireland", "Croatia", 
                     "Moldova", "Bosnia and Herzegovina", "Albania", "Lithuania", "Slovenia",
                     "North Macedonia", "Latvia", "Estonia", "Montenegro", "Luxembourg",
                     "Malta", "Iceland", "Andorra", "Monaco", "Liechtenstein",
                     "San Marino", "Russia", "Belarus",
                     
                     "China", "India", "Indonesia", "Pakistan", "Bangladesh",
                     "Japan", "Philippines", "Vietnam", "Turkey", "Iran",
                     "Thailand", "Myanmar", "South Korea", "Iraq", "Afghanistan",
                     "Saudi Arabia", "Uzbekistan", "Malaysia", "Yemen", "Nepal",
                     "North Korea", "Sri Lanka", "Kazakhstan", "Syria", "Cambodia",
                     "Jordan", "Azerbaijan", "United Arab Emirates", "Tajikistan", "Laos",
                     "Israel", "Lebanon", "Kyrgyzstan", "Turkmenistan", "Singapore",
                     "Oman", "Palestine", "Kuwait", "Georgia", "Mongolia",
                     "Armenia", "Qatar", "Bahrain", "Timor-Leste", "Cyprus",
                     "Bhutan", "Maldives", "Brunei", "Taiwan", "Hong Kong"))
country_code %>% filter(name == "China")
country_code %>% filter(code == "KH")
from <- tibble(from_code = country_code$code,
               from_country = country_code$name)
to <- tibble(to_code = country_code$code,
             to_country = country_code$name)
eur_asia_routes <- expand.grid(from$from_code, to$to_code)
eur_asia_routes <- eur_asia_routes %>%
  rename(from_code = Var1,
         to_code = Var2)
routes_df <- inner_join(eur_asia_routes, from, by = "from_code")  
routes_df <- inner_join(routes_df, to, by = "to_code")
routes_df_europe <- read_csv("routes_df_europe.csv")
except_european <- anti_join(routes_df, routes_df_europe)


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

links_plane <- paste0("https://api.tequila.kiwi.com/v2/search?fly_from=", except_european$from_code, 
                      "&fly_to=", except_european$to_code, 
                      "&date_from=30%2F06%2F2023&date_to=30%2F12%2F2023&curr=EUR&vehicle_type=aircraft&limit=1000") 


dataset_of_flights <- tibble()
for (i in 1:length(links_plane)) {
  data <- api_call_vital(links_plane[i])
  Sys.sleep(2.0)
  dataset_of_flights <- rbind(dataset_of_flights, data)
}

proc <- dataset_of_flights %>%
  group_by(cityFrom, cityTo) %>%
  slice(which.min(price_EUR))
write_csv(proc, "kiwi_europe_asia_countries_filght_processed.csv")


proc %>%
  group_by(cityFrom, cityTo) %>%
  count() %>%
  arrange(desc(n))
proc %>% 
  group_by(cityFrom, cityTo) %>%
  count() %>%
  filter(n > 1)

# Processing
set1 <- read_csv("kiwi_europe_asia_countries_filght_processed.csv")
set2 <- read_csv("kiwi_europe_asia_countries_filght_processed2.csv")
set3 <- read_csv("kiwi_europe_asia_countries_filght_processed3.csv")
set4 <- read_csv("kiwi_europe_asia_countries_filght_processed4.csv")
set5 <- read_csv("kiwi_europe_country_flights_processed.csv")
set_asia_eur <- rbind(set1, set2, set3, set4, set5) %>%
  group_by(cityFrom, cityTo) %>%
  slice(which.min(price_EUR))
write_csv(set_asia_eur, "kiwi_asia_europe_filght.csv")
# Countries
europe1 <- read_csv("kiwi_europe_country_bus_processed.csv")
europe2 <- read_csv("kiwi_europe_country_train_processed.csv")
europe <- rbind(set5, europe1, europe2) %>%
  select(cityFrom, cityTo, countryFrom, countryTo)
e1 <- europe[,c(1,3)] %>%
  rename(city = cityFrom,
         country = countryFrom)
e2 <- europe[,c(2,4)] %>%
  rename(city = cityTo,
         country = countryTo)
eurupe_all_cities <- rbind(e1, e2) %>%
  distinct()


asia <- set_asia_eur %>%
  select(cityFrom, cityTo, countryFrom, countryTo)
as1 <- asia[,c(1,3)] %>%
  rename(city = cityFrom,
         country = countryFrom)
as2 <- asia[,c(2,4)] %>%
  rename(city = cityTo,
         country = countryTo)
asia_all_cities <- rbind(as1, as2) %>%
  distinct()
asia_europe_cities <- rbind(asia_all_cities, eurupe_all_cities) %>%
  distinct()
write_csv(asia_europe_cities, "kiwi_asia_europe_cities.csv")

