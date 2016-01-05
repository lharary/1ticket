import java.io.*;//specify the import statements needed to use
import java.util.Scanner;//a Scanner object and File objects
import java.util.*;


public class emailScript3 {
	public static void main(String[] args) throws IOException {
		String myDirectory = "/Users/Leon/Desktop/consulting/Archive/messages";
		runParser(myDirectory);
	}
	//method runs the parser through directory thats input as a String as argument
	public static void runParser(String directory)throws IOException{
		int index = 1;
		File[] files = new File(directory).listFiles();
		while (index<files.length){
			System.out.println(index);
			System.out.println(files[index]);
			printData(files[index]);
			System.out.println("");
			index ++;
		}
	}

	
	public static void showFiles(File[] files) throws IOException {//method that shows each file in directory
  //method shows each file in a directory, used to pass through each email
    	for (File file : files) {
        if (file.isDirectory()) {
            showFiles(file.listFiles()); // Calls same method again.
        } else {
           System.out.println("File: " + file.getName());
        }
    	}
	}

	public static void printData(File email) throws IOException{
		//method parses through email to return relevant information about the order
		//input is an email file

		//bring in scanner
		Scanner in = new Scanner(email);
		int line = 1;
		String subject = in.nextLine();
		//checking if file is an email that should be parsed 
		if (!subject.contains("Your Ticketmaster Order")) {
			return;
		}

		//defining a valid order date
		String orderDate = in.nextLine();
		while (validateOrderDate(orderDate)==false){
			orderDate =in.nextLine();
			//line ++;
		}
		
		// defining a valid order #
		String orderNumber = in.nextLine();
		while (validateOrderNumber(orderNumber)==false){
			orderNumber = in.nextLine();
		}
		
		//defining event, location, date, and reaching first ticket line
		String line25 = in.nextLine();
		while (validateEvent(subject, line25)==false){
			line25 = in.nextLine();
		}
		String line26 = in.nextLine(); 
		String line27 = in.nextLine(); 
		String line28 = in.nextLine(); 
		String line29 = in.nextLine();
		String line30 = in.nextLine();
		String line31 = in.nextLine();

		String event;
		String location;
		String eventDate;
		int scenario;//used to distinguish line splits for event/location
		String firstTicket;
		//validating event, and accounting for two lined events and locations
		//then defining event date
		if (line30.isEmpty()) {//one line each for event, location, and date
			event = line25;
			location = line26;
			eventDate = line27;
			scenario = 1;
			firstTicket = line29;
		}else {
			event = line25+" "+line26;//two lines for event
			location = line27;
			eventDate = line28;
			scenario = 2;
			firstTicket = line30;
		}
		if (validateEvent(subject, event)==false) {//two lines for location
			event = line25;
			location = line26 + " "+line27;
			eventDate = line28;
			scenario = 2;
			firstTicket = line30;
		}
		if (validateEventDate(eventDate)==false) {//two lines for event and location
			event = line25+" "+line26;
			location = line27 + " "+line28;
			eventDate = line29;
			scenario = 3;
			firstTicket = line31;
		}

		//creating state from last two characters, for validation
		char state1 = location.charAt(location.length()-1);
		char state2 = location.charAt(location.length()-2);
		String state = "";
		location = location.trim();
		state = state1 + state;
		state = state2 + state;
		validateState(state);
		
		
		//defining and adding in count of tickets
		int ticketCount = 1;
		while (validateTicket(firstTicket)==false){
			firstTicket =in.nextLine();
		}
		String next = in.nextLine();
		while(!next.contains("Total Charges:")==true){
			if (next.contains("Section")) {
				ticketCount++;
				next = in.nextLine();
			}else{
				next = in.nextLine();
			}
		}

		//adding in price
		String pricePaid = in.nextLine();
		pricePaid = pricePaid.trim();
		


		//printing output and validation checks
		System.out.println("tickets: "+ticketCount);
		System.out.println(firstTicket);
		System.out.println(subject);
		System.out.println(orderNumber);
		System.out.println("Order Date: "+orderDate);
		System.out.println("Event: "+event);
		System.out.println("Location: "+location);
		System.out.println("Event Date: "+ eventDate);
		System.out.println("Price Paid: "+pricePaid);
		System.out.println("Tickets purchased: ");
		System.out.println("Subject Validated: "+validateSubject(subject));
		System.out.println("Order Number Validated: "+validateOrderNumber(orderNumber));
		System.out.println("Order Date Validated: "+validateOrderDate(orderDate));
		System.out.println("Event Validated: "+validateEvent(subject, event));
		System.out.println("Location Validated: "+validateState(state));
		System.out.println("Event Date Validated: "+validateEventDate(eventDate));
		System.out.println("Price Validated: "+validatePrice(pricePaid));
		validateAll(subject, event, eventDate, state, pricePaid);
	}

	//chain of ifs on all validations with quits and error messages
	// inputs are strings of subject, event, eventdate, state abbrev, and price
	public static Boolean validateAll(String subj, String ev, String eDate, String sta, String pri){
		if (validateSubject(subj)==false) {//validating subject
			System.out.println("Error: Subject not valid");
			System.exit(1);
		}
		if (validateEvent(subj, ev)==false) {// validating event
			System.out.println("Error: Event not valid");
			System.exit(1);
		}
		if (validateEventDate(eDate)==false) {// validating event date
			System.out.println("Error: Event Date not valid");
			System.exit(1);
		}
		if (validateState(sta)==false) {// validating state at end of location (canada included. boo canada)
			System.out.println("Warning - State not validated ("+sta+")");
		}
		if (validatePrice(pri)==false) {//validating price
			System.out.println("Error: Price not valid");
		}
		return true;
	}

	//validating price based on containing a dollar sign and period
	// input is string, price
	public static Boolean validatePrice(String pri){
		if (pri.contains("$")==true && pri.contains(".")==true) {
			return true;
		}else{
			System.exit(2);
			return false;
		}
	}

	//validating tickets, based on containing "Section"
	//input is string of ticket information
	public static Boolean validateTicket(String tick){
		if (tick.contains("Section")) {
			return true;
		}else{
			return false;
		}
	}

	// validating state, based on Last two letters of location
	//input is a string, state code
	public static Boolean validateState(String sta){
		String[] states = {"AB","BC","MB","NB","NL","NT","NS","NU","ON","PE","QC","SK","YT","AA","OR","AE","AP","AL","AK","AS","AZ","AR","CA","CO","CT","DE","DC","FM","FL","GA","GU","HI","ID","IL","IN","IA","KS","KY","LA","ME","MH","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","MP","OH","OK","OR","PW","PA","PR","RI","SC","SD","TN","TX","UT","VT","VI","VA","WA","WV","WI","WY"};
		List <String> listStates = Arrays.asList(states);
		Set<String> setStates = new HashSet<String>(listStates);
		if (setStates.contains(sta)==true) {
			return true;
		}else{
			
			System.exit(2);
			return false;
		}
		//return true;
	}

	// validating event, based on subject containing event
	//inputs are string, subject, and string, event
	public static Boolean validateEvent(String subj, String event){
		if (event.isEmpty()) {
			return false;
		}
		if (subj.contains(event)){
			return true;
		}
		else{
			return false;
		}
	}

	// validating subject, containing "Subject:"
	//input is string, subject
	public static Boolean validateSubject(String subj){
		if (subj.contains("Subject: Your Ticketmaster Order ")) {
			return true;
		}else{
			return false;
		}
	}

	// validating order #, containing "Order #"
	//input is string, order number
	public static Boolean validateOrderNumber(String ord){
		if (ord.contains("Order #:")) {
			//orderFail = orderFail + 1;
			return true;
		}
		else{
			//orderPass = orderPass + 1;
			return false;
		}
	}

	// validating order date, containing full month name
	//input is string, order date
	public static Boolean validateOrderDate(String date){
		if ((date.contains("January")) || (date.contains("February")) ||(date.contains("March")) ||(date.contains("April")) ||(date.contains("May")) ||(date.contains("June")) ||(date.contains("July")) ||(date.contains("August")) ||(date.contains("September")) ||(date.contains("October")) ||(date.contains("November")) ||(date.contains("December"))){
			return true;
		}
		else{
			return false;
		}
	}

	// validating event date, containing year, month (abbrev), AM/PM, and day of week (abbrev)
	//input is string, event date
	public static Boolean validateEventDate(String date){
		if ((date.contains("Jan")) || (date.contains("Feb")) ||(date.contains("Mar")) ||(date.contains("Apr")) ||(date.contains("May")) ||(date.contains("Jun")) ||(date.contains("Jul")) ||(date.contains("Aug")) ||(date.contains("Sep")) ||(date.contains("Oct")) ||(date.contains("Nov")) ||(date.contains("Dec"))) {
			int x = 1;
		}else {
			System.out.println("Error: Invalid Date(month)");
			System.exit(1);
			return false;
		}
		if ((date.contains("2014"))||(date.contains("2015"))||(date.contains("2016"))||(date.contains("2017"))) {
			int y = 2;
		}else{
			System.out.println("Error: Invalid Date(Year)");
			return false;
		}
		if ((date.contains("PM")) || (date.contains("AM"))) {
			int z = 3;
		}else{
			System.out.println("Error: Invalid Date(AM/PM)");
			return false;
		}if ((date.contains("Sun,"))||(date.contains("Mon,"))||(date.contains("Tue,"))||(date.contains("Wed,"))||(date.contains("Thu,"))||(date.contains("Fri,"))||(date.contains("Sat,"))) {
			return true;
		}else{
			System.out.println("Error: Invalid Date(Day of Week)");
			return false;
		}
	}
}

