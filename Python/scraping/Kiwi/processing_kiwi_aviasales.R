library(tidyverse)
library(jsonlite)
# Get list of cities
europe_f <- read_csv("kiwi_europe_country_flights_processed.csv")
europe_t <- read_csv("kiwi_europe_country_train_processed.csv")
europe_b <- read_csv("kiwi_europe_country_bus_processed.csv")
a_e<- read_csv("kiwi_america+asia+europe_filghts.csv")
a_e_f <- read_csv("kiwi_asia_europe_filght.csv")
a_e_b <- read_csv("kiwi_asia_europe_bus.csv")
a_e_t <- read_csv("kiwi_asia_europe_train.csv")
a_f <- read_csv("kiwi_north_america_countries_filghts.csv")
a_b <- read_csv("kiwi_north_america_countries_bus.csv")
a_t <- read_csv("kiwi_north_america_countries_train.csv")

df <- rbind(a_e, europe_f, europe_t, europe_b, a_e_f, a_e_b, a_e_t, a_f, a_b, a_t)
df1<- df %>% 
  select(cityFrom, countryFrom) %>% 
  rename(city = cityFrom,
         country = countryFrom)
df2<- df %>% 
  select(cityTo, countryTo) %>% 
  rename(city = cityTo,
         country = countryTo)
df_new <- rbind(df1,df2)
df_new <- df_new %>%
  distinct()
write_csv(df_new, "kiwi_asia_europe_north_america_cities.csv")


aviasales <- read_csv('aviasales_flights_all.csv')
aviasales %>%
  filter(from_country =='Russia') %>%
  View()

# Merge data from kiwi and aviasales, bring in to the standard form
europe_fl <- read_csv("kiwi_europe_country_flights_processed.csv")
europe_tr <- read_csv("kiwi_europe_country_train_processed.csv")
europe_bu <- read_csv("kiwi_europe_country_bus_processed.csv")

europe_fl <- europe_fl %>%
  mutate(transport_id = 1)
europe_tr <- europe_tr %>%
  mutate(transport_id = 3)
europe_bu <- europe_bu %>%
  mutate(transport_id = 2)
europe_full <- rbind(europe_fl, europe_tr, europe_bu) %>%
  rename(from_city = cityFrom,
         to_city = cityTo,
         duration = durationDepatrure) %>%
  select(from_city, 
         to_city,
         transport_id,
         price_EUR,
         distance,
         duration)
  
europe_full <- europe_full %>%
  mutate(duration_min = duration/60) %>%
  select(-duration)

asia_eur_fl <- read_csv("kiwi_asia_europe_filght.csv") %>%
  mutate(transport_id = 1)
asia_eur_bu <- read_csv("kiwi_asia_europe_bus.csv") %>%
  mutate(transport_id = 2)
asia_eur_tr <- read_csv("kiwi_asia_europe_train.csv") %>%
  mutate(transport_id = 3)
asia_eur_full <- rbind(asia_eur_fl, asia_eur_bu, asia_eur_tr) %>%
  rename(from_city = cityFrom,
         to_city = cityTo,
         duration = durationDepatrure) %>%
  select(from_city, 
         to_city,
         transport_id,
         price_EUR,
         distance,
         duration) %>%
  mutate(duration_min = duration/60) %>%
  select(-duration)


america_eurasia_fl<- read_csv("kiwi_america+asia+europe_filghts.csv") %>%
  mutate(transport_id = 1)
america_fl <- read_csv("kiwi_north_america_countries_filghts.csv") %>%
  mutate(transport_id = 1)
america_bu <- read_csv("kiwi_north_america_countries_bus.csv") %>%
  mutate(transport_id = 2)
america_tr <- read_csv("kiwi_north_america_countries_train.csv") %>%
  mutate(transport_id = 3)

america_full <- rbind(america_eurasia_fl, america_fl, america_bu, america_tr) %>%
  rename(from_city = cityFrom,
         to_city = cityTo,
         duration = durationDepatrure) %>%
  select(from_city, 
         to_city,
         transport_id,
         price_EUR,
         distance,
         duration) %>%
  mutate(duration_min = duration/60) %>%
  select(-duration)


full_data <- rbind(europe_full, asia_eur_full, america_full) %>%
  distinct()


from_Rus <- read_csv('Moscow_world.csv') %>%
  mutate(transport_id = 1)
to_Rus <- read_csv('world_Moscow.csv') %>%
  mutate(transport_id = 1)
rus <- rbind(from_Rus, to_Rus) %>%
  select(from_city,
         to_city,
         transport_id,
         price,
         duration) %>%
  rename(price_EUR = price,
         duration_min = duration)


full_data <- full_data %>%
  select(-distance)

whole <- rbind(full_data, rus)

id <- fromJSON("some info about new locations/archive/json/locations.json") %>%
  as_tibble()
id <- id[1,]
id <- id %>%
  mutate(variables = 'city')

id_df <- id %>%
  pivot_longer(cols = -variables,
               names_to = c("key"),
               values_to = c("other")) %>%
  pivot_wider(names_from = variables,
              values_from = other)
id_df$city <- as.character(id_df$city)
id_df$key <- as.numeric(id_df$key)

from_id <- left_join(whole, id_df, by = c('from_city' = 'city'))
from_id <- from_id %>%
  rename(from_id = key)

to_id <- left_join(from_id, id_df, by = c('to_city' = 'city'))
to_id <- to_id %>%
  rename(to_id = key)
write_csv(to_id, 'procecced_routes_america_europe_asia_with_ids.csv')
