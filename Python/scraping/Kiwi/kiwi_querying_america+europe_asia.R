library(tidyverse)
library(httr)

c_code <- GET("http://api.travelpayouts.com/data/en/countries.json")
c_code_resp <- jsonlite::fromJSON(rawToChar(c_code$content))
country_code_sub <- c_code_resp %>%
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
                     "Saint Barthélemy", "Saint Pierre and Miquelon", "Montserrat",
                     
                     "Germany", "United Kingdom", "France", "Italy", "Spain",
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

from <- tibble(from_code = country_code_sub$code,
               from_country = country_code_sub$name)
to <- tibble(to_code = country_code_sub$code,
             to_country = country_code_sub$name)
amer_eur_asia_routes <- expand.grid(from$from_code, to$to_code)
amer_eur_asia_routes <- amer_eur_asia_routes %>%
  rename(from_code = Var1,
         to_code = Var2)
all_routes_df <- inner_join(amer_eur_asia_routes, from, by = "from_code")  
all_routes_df <- inner_join(all_routes_df, to, by = "to_code")
compl_df <- anti_join(all_routes_df, routes_df_europe)
compl_df <- anti_join(compl_df, NA_df)
compl_df <- anti_join(compl_df, except_european)
write_csv(compl_df, "america_europe+asia_routes.csv")


routes_data <- read_csv("america_europe+asia_routes.csv")
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

links_plane <- paste0("https://api.tequila.kiwi.com/v2/search?fly_from=", routes_data$from_code, 
                      "&fly_to=", routes_data$to_code, 
                      "&date_from=30%2F07%2F2023&date_to=30%2F12%2F2023&curr=EUR&vehicle_type=aircraft&limit=1000") 


dataset_of_flights <- tibble()
for (i in 1:length(links_plane)) {
  data <- api_call_vital(links_plane[i])
  Sys.sleep(2.0)
  dataset_of_flights <- rbind(dataset_of_flights, data)
}

proc <- dataset_of_flights %>%
  group_by(cityFrom, cityTo) %>%
  slice(which.min(price_EUR)) %>%
  distinct()
write_csv(proc, "kiwi_america+asia+europe_filghts.csv")
