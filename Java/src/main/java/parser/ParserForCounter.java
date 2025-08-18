package parser;

import functional.classes.Location;
import functional.classes.TravelData;
import maker.classes.OldLocationsMaker;
import visual.Console;
import visual.MenuInitializer;

import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class ParserForCounter {

	public static Console console = MenuInitializer.console;
	public static PrintStream stream = new PrintStream(console);

	public static String[] CSVoString(String fileName) throws IOException {
		File file = new File(fileName);
		FileReader fr = new FileReader(file);
		BufferedReader reader = new BufferedReader(fr);
		StringBuilder line = new StringBuilder("");
		String add = "";
		while (add != null) {
			String str = "";
			add = reader.readLine();
			if (add == null) {
				str = "";
			} else {
				str = "(" + add + "),";
			}
			line.append(str);
		}

		String[] lines = line.toString().split("\\),\\(");
		for (int i = 0; i < lines.length; i++) {
			lines[i] = lines[i].replaceAll("[(')]", "");
			lines[i] = lines[i].replaceAll("null", "");
		}
		return lines;
	}

	public static ArrayList<Location> insertLocations(String[] input) {
		
		Map<Integer, String> countries = getCountries();
		int k = input.length;
		ArrayList<Location> locations = new ArrayList<>();
		for (int i = 0; i < k; i++) {
			String[] arr = input[i].split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)");
			try {
				int id = Integer.parseInt(arr[0]);
				String name = arr[1];
				double latitude = Float.parseFloat(arr[2]);
				double longitude = Float.parseFloat(arr[3]);
				String country_name = countries.get(Integer.parseInt(arr[4]));
				Location result = new Location(id, name, latitude, longitude, country_name);
				locations.add(result);
			} catch (NumberFormatException e) {

			}

		}
		stringMaker("Locations successfully parsed");
		return locations;
	}

	public static Map<Integer, String> getCountries() {
		Path currentDirectory = Paths.get("").toAbsolutePath();
		HashMap<Integer, String> countries = new HashMap<Integer, String>();
		try (BufferedReader reader = new BufferedReader(
				new FileReader(new File(currentDirectory + "\\data_files\\" + "countries.csv")));) {
			String line = null;
			while ((line = reader.readLine()) != null) {
				try {
					String[] arr = line.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)");
					int countruId = Integer.parseInt(arr[0]);
					countries.put(countruId, arr[1]);
				} catch (NumberFormatException e) {
					continue;
				}

			}
		} catch (Exception e) {
			System.out.println("Attempt to parse countries failed");
			e.printStackTrace();
		}
		return countries;
	}

	public static ArrayList<TravelData> insertTravelData(String[] input) {
		int k = input.length;
		ArrayList<TravelData> datas = new ArrayList<>();
		for (int i = 0; i < k; i++) {
			if (!input[i].startsWith("path_id")) {
				String[] arr = input[i].split(",");
				TravelData data = new TravelData(Integer.parseInt(arr[0]), Integer.parseInt(arr[1]),
						Integer.parseInt(arr[2]), Integer.parseInt(arr[3]), Float.parseFloat(arr[4]),
						Integer.parseInt(arr[5]));
				datas.add(data);
			}
		}
		stringMaker("Direct routes successfully parsed");
		return datas;
	}

	public static String locationsToString(ArrayList<Location> list) {
		String result = "";
		for (int i = 0; i < list.size(); i++) {
			Location location = list.get(i);
			String add = "Id = " + location.getId() + "," + "Name = " + location.getName() + "," + "Latitude = "
					+ location.getLatitude() + "," + "Longitude = " + location.getLongitude() + "\n";
			result = result + add;
		}
		return result;
	}

	public static String travelDataToString(ArrayList<TravelData> list) {
		String result = "";
		for (int i = 0; i < list.size(); i++) {
			TravelData directRoute = list.get(i);
			String add = "Id = " + directRoute.getId() + "," + "`from` = " + directRoute.getFrom() + "," + "`to` = "
					+ directRoute.getTo() + "," + "transportation_type = " + directRoute.getTransportation_type() + ","
					+ "euro_price = " + directRoute.getEuro_price() + "," + "time_in_minutes = "
					+ directRoute.getTime_in_minutes() + "\n";
			result = result + add;
		}
		return result;
	}

	public static HashMap<Integer, Integer> parseRoutesForValidation(String csvFolderPath, String routesType) {
		try (BufferedReader reader = new BufferedReader(
				new FileReader(new File(csvFolderPath + "\\" + routesType + ".csv")));) {
			HashMap<Integer, Integer> counter = new HashMap<Integer, Integer>();
			String line;
			while ((line = reader.readLine()) != null || line != null) {
				line = line.substring(1, line.length() - 3);
				String[] lines = line.split("\\),\\(");
				for (int i = 0; i < lines.length; i++) {
					String[] cells = lines[i].split(",");
					for (int j = 4; j < cells.length; j++) {
						int edgeId = Integer.parseInt(cells[j]);
						counter.computeIfPresent(edgeId, (key, val) -> val += 1);
						counter.computeIfAbsent(edgeId, key -> 1);
					}
				}
			}
			return counter;
		} catch (Exception e) {
			e.printStackTrace();
		}

		return null;
	}

	public static void stringMaker(String input) {
		System.out.println(input);
		stream.println(input);
	}
}
