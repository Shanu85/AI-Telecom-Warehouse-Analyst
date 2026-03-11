STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "Gujarat",
    "Rajasthan", "West Bengal", "Andhra Pradesh", "Telangana", "Kerala",
    "Madhya Pradesh", "Bihar", "Punjab", "Haryana", "Delhi",
    "Odisha", "Assam", "Jharkhand", "Uttarakhand", "Himachal Pradesh",
    "Jammu & Kashmir", "Goa"
]

STATE_CITIES = {
    "Maharashtra":      ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Amravati", "Kolhapur", "Thane", "Navi Mumbai"],
    "Karnataka":        ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi", "Kalaburagi", "Davanagere", "Ballari", "Tumkur", "Udupi"],
    "Tamil Nadu":       ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli", "Tiruppur", "Vellore", "Erode", "Thoothukudi"],
    "Uttar Pradesh":    ["Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj", "Meerut", "Ghaziabad", "Noida", "Bareilly", "Moradabad"],
    "Gujarat":          ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Junagadh", "Gandhinagar", "Anand", "Bharuch"],
    "Rajasthan":        ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer", "Bhilwara", "Alwar", "Sikar", "Pali"],
    "West Bengal":      ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri", "Bardhaman", "Malda", "Baharampur", "Habra", "Kharagpur"],
    "Andhra Pradesh":   ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Tirupati", "Rajahmundry", "Kakinada", "Eluru", "Ongole"],
    "Telangana":        ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam", "Ramagundam", "Mahbubnagar", "Nalgonda", "Adilabad", "Suryapet"],
    "Kerala":           ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Palakkad", "Alappuzha", "Malappuram", "Kannur", "Kasaragod"],
    "Madhya Pradesh":   ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Dewas", "Satna", "Ratlam", "Rewa"],
    "Bihar":            ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", "Darbhanga", "Bihar Sharif", "Arrah", "Begusarai", "Katihar"],
    "Punjab":           ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali", "Firozpur", "Pathankot", "Hoshiarpur", "Moga"],
    "Haryana":          ["Faridabad", "Gurugram", "Panipat", "Ambala", "Yamunanagar", "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula"],
    "Delhi":            ["New Delhi", "Dwarka", "Rohini", "Janakpuri", "Laxmi Nagar", "Saket", "Pitampura", "Karol Bagh", "Shahdara", "Vasant Kunj"],
    "Odisha":           ["Bhubaneswar", "Cuttack", "Rourkela", "Brahmapur", "Sambalpur", "Puri", "Balasore", "Bhadrak", "Baripada", "Jharsuguda"],
    "Assam":            ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Nagaon", "Tinsukia", "Tezpur", "Bongaigaon", "Dhubri", "Diphu"],
    "Jharkhand":        ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar", "Phusro", "Hazaribagh", "Giridih", "Ramgarh", "Medininagar"],
    "Uttarakhand":      ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", "Kashipur", "Rishikesh", "Pithoragarh", "Ramnagar", "Mussoorie"],
    "Himachal Pradesh": ["Shimla", "Dharamshala", "Solan", "Mandi", "Baddi", "Nahan", "Palampur", "Sundarnagar", "Chamba", "Una"],
    "Jammu & Kashmir":  ["Srinagar", "Jammu", "Anantnag", "Baramulla", "Sopore", "Kathua", "Udhampur", "Punch", "Rajouri", "Leh"],
    "Goa":              ["Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda", "Bicholim", "Curchorem", "Sanquelim", "Cuncolim", "Canacona"],
}

OPERATORS = ["Jio", "Airtel", "Vi", "BSNL", "MTNL"]

# Market share base % per operator 
OPERATOR_SHARE_BASE = {
    "Jio":    35,
    "Airtel": 30,
    "Vi":     18,
    "BSNL":   12,
    "MTNL":    5,
}

# State-level population weight (bigger states → more subscribers)
STATE_WEIGHT = {
    "Uttar Pradesh": 2.5, "Maharashtra": 2.2, "West Bengal": 1.8,
    "Bihar": 1.7, "Tamil Nadu": 1.6, "Rajasthan": 1.5,
    "Karnataka": 1.4, "Gujarat": 1.3, "Andhra Pradesh": 1.2,
    "Telangana": 1.1, "Madhya Pradesh": 1.1, "Kerala": 1.0,
    "Delhi": 1.8, "Punjab": 0.9, "Haryana": 0.9,
    "Odisha": 0.8, "Assam": 0.7, "Jharkhand": 0.7,
    "Uttarakhand": 0.5, "Himachal Pradesh": 0.4,
    "Jammu & Kashmir": 0.4, "Goa": 0.2,
}
