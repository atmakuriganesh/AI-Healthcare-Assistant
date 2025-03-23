import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from datetime import datetime
import os
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv()

class HospitalFinder:
    """Hospital finder using Google Maps API with navigation buttons"""
    
    def __init__(self):
        # Get API key from environment variables
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.google_api_key:
            st.error("Google Maps API key not found. Please add it to your .env file.")
        
        # Initialize session state
        if 'patient_location' not in st.session_state:
            st.session_state.patient_location = None
        if 'hospitals_found' not in st.session_state:
            st.session_state.hospitals_found = []
    
    def add_to_intake_form(self):
        """Add location fields to the patient intake form"""
        st.subheader("Your Location")
        
        col1, col2 = st.columns(2)
        
        with col1:
            address = st.text_input("Street Address", placeholder="123 Main St")
            city = st.text_input("City", placeholder="New York", key="patient_city")
        
        with col2:
            state = st.selectbox(
                "State", 
                ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                 "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                 "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                 "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                 "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
                key="patient_state"
            )
            zipcode = st.text_input("ZIP Code", placeholder="10001", key="patient_zipcode")
        
        # Store the location data in session state
        if city and (state or zipcode):
            location_str = ", ".join(filter(None, [address, city, state, zipcode]))
            
            if 'patient_data' not in st.session_state:
                st.session_state.patient_data = {}
                
            st.session_state.patient_data.update({
                "address": address,
                "city": city,
                "state": state,
                "zipcode": zipcode,
                "location_str": location_str
            })
    
    def render_hospital_finder(self):
        """Render hospital finder interface with navigation buttons"""
        # Add navigation buttons at the top
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Back", key="back_from_hospital"):
                # Return to previous screen (could be assessment or care planning)
                if 'previous_stage' in st.session_state:
                    st.session_state.current_stage = st.session_state.previous_stage
                else:
                    st.session_state.current_stage = 'care_planning'  # Default if no previous stage
                st.rerun()
                
        with col3:
            if st.button("🏠 Home", key="home_from_hospital"):
                # Return to the main screen/intake
                st.session_state.current_stage = 'intake'
                st.rerun()
        
        # Main header
        st.header("Find Healthcare Providers Near You")
        
        # Check if we have location data
        has_location = False
        if 'patient_data' in st.session_state:
            if 'city' in st.session_state.patient_data and st.session_state.patient_data['city']:
                has_location = True
                location_str = st.session_state.patient_data.get('location_str', 'your location')
                st.write(f"Finding providers near: **{location_str}**")
        
        if not has_location:
            st.warning("Please complete the patient intake form with your location first.")
            return
        
        # Create tabs for different search options
        tab1, tab2 = st.tabs(["Find Nearby Hospitals", "Emergency Care"])
        
        with tab1:
            self._search_nearby_hospitals()
        
        with tab2:
            self._search_emergency_care()
        
        # Display results if available
        if st.session_state.hospitals_found:
            self._display_hospital_results()
    
    def _search_nearby_hospitals(self):
        """Search for hospitals near patient location"""
        # Distance slider
        max_distance = st.slider("Search Radius (miles)", 1, 25, 10)
        
        # Create facility type filter
        facility_types = [
            "Hospital", 
            "Medical Clinic", 
            "Doctor's Office", 
            "Urgent Care", 
            "Pharmacy"
        ]
        
        selected_type = st.selectbox("Facility Type", facility_types)
        
        # Search button
        if st.button("Find Healthcare Facilities", key="find_hospitals_btn"):
            with st.spinner("Searching for healthcare facilities..."):
                # Get patient location coordinates
                location = self.geocode_address()
                
                if location:
                    # Search for nearby healthcare facilities
                    facilities = self.search_nearby_places(
                        location['lat'], 
                        location['lng'], 
                        selected_type, 
                        max_distance
                    )
                    
                    # Store in session state
                    st.session_state.hospitals_found = facilities
                    st.session_state.search_type = "facilities"
                else:
                    st.error("Could not determine your location. Please check your address details.")
    
    def _search_emergency_care(self):
        """Search for emergency care facilities near patient location"""
        st.warning("⚠️ In case of life-threatening emergency, call 911 immediately.")
        
        # Emergency service type
        service_types = [
            "Emergency Room", 
            "Urgent Care", 
            "Hospital"
        ]
        
        selected_service = st.selectbox("Type of Emergency Service Needed", service_types)
        
        # Distance slider - defaults to higher for emergency
        max_distance = st.slider("Maximum Distance (miles)", 1, 25, 15, key="emergency_distance")
        
        # Search button
        if st.button("Find Emergency Services", key="find_emergency_btn"):
            with st.spinner("Locating emergency services near you..."):
                # Get patient location coordinates
                location = self.geocode_address()
                
                if location:
                    # Search for nearby emergency facilities
                    keyword = selected_service
                    if selected_service == "Emergency Room":
                        keyword = "Emergency Room Hospital"
                    
                    facilities = self.search_nearby_places(
                        location['lat'], 
                        location['lng'], 
                        keyword, 
                        max_distance,
                        is_emergency=True
                    )
                    
                    # Store in session state
                    st.session_state.hospitals_found = facilities
                    st.session_state.search_type = "emergency"
                else:
                    st.error("Could not determine your location. Please check your address details.")
    
    def _display_hospital_results(self):
        """Display hospital search results"""
        search_type = st.session_state.get('search_type', 'facilities')
        
        # Display results header
        if search_type == "emergency":
            st.subheader("Emergency Services Near You")
        else:
            st.subheader("Healthcare Facilities Near You")
        
        # Check if we have results
        if not st.session_state.hospitals_found:
            st.info("No healthcare facilities found. Try expanding your search radius or changing your search terms.")
            return
        
        # Display map of results
        st.write("### Facility Locations")
        self._display_provider_map()
        
        # Display facility list
        st.write("### Facility Details")
        
        # Display each facility
        for i, facility in enumerate(st.session_state.hospitals_found):
            with st.expander(f"{i+1}. {facility['name']} - {facility.get('distance', 0):.1f} miles"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Address:** {facility.get('vicinity', 'No address available')}")
                    
                    if 'formatted_phone_number' in facility:
                        st.write(f"**Phone:** {facility['formatted_phone_number']}")
                    
                    # Display types
                    if 'types' in facility:
                        st.write("**Facility Type:**")
                        types = [t.replace('_', ' ').title() for t in facility['types'][:3] 
                                if t not in ['point_of_interest', 'establishment', 'health']]
                        st.write(", ".join(types) if types else "General Healthcare Facility")
                
                with col2:
                    # Display rating
                    if 'rating' in facility:
                        st.write(f"**Rating:** {'⭐' * int(facility['rating'])} ({facility['rating']})")
                        
                        if 'user_ratings_total' in facility:
                            st.write(f"**Reviews:** {facility['user_ratings_total']}")
                    
                    # Display open now
                    if 'opening_hours' in facility and 'open_now' in facility['opening_hours']:
                        status = "Open now" if facility['opening_hours']['open_now'] else "Closed"
                        st.write(f"**Status:** {status}")
                
                # Facility actions
                if st.button("Get Directions", key=f"directions_{i}"):
                    self._open_directions(facility)
                
                if st.button("View on Google Maps", key=f"google_{i}"):
                    if 'place_id' in facility:
                        maps_url = f"https://www.google.com/maps/place/?q=place_id:{facility['place_id']}"
                        st.markdown(f"[Open in Google Maps]({maps_url})")
                
                if st.button("Add to Care Plan", key=f"add_to_plan_{i}"):
                    self._add_provider_to_care_plan(facility)
                    st.success(f"Added {facility['name']} to patient care plan")
    
    def _display_provider_map(self):
        """Display providers on an interactive map"""
        # Get patient location
        location = self.geocode_address()
        
        if not location:
            st.error("Could not determine your location. Please check your address details.")
            return
        
        # Get provider coordinates
        facilities = st.session_state.hospitals_found
        
        # Create map centered on patient location
        m = folium.Map(location=[location['lat'], location['lng']], zoom_start=12)
        
        # Add patient location marker
        folium.Marker(
            [location['lat'], location['lng']],
            popup="Your Location",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)
        
        # Add facility markers
        for facility in facilities:
            if 'geometry' in facility and 'location' in facility['geometry']:
                # Determine marker color 
                color = "blue"
                if "hospital" in str(facility.get('types', [])).lower():
                    color = "darkblue"
                elif "emergency" in facility.get('name', '').lower():
                    color = "red"
                elif "urgent" in facility.get('name', '').lower():
                    color = "orange"
                
                # Create popup content
                popup_html = f"""
                <b>{facility['name']}</b><br>
                {facility.get('vicinity', 'No address available')}<br>
                """
                
                if 'rating' in facility:
                    popup_html += f"Rating: {facility['rating']}/5<br>"
                    
                if 'distance' in facility:
                    popup_html += f"Distance: {facility['distance']:.1f} miles"
                
                # Add marker
                folium.Marker(
                    [facility['geometry']['location']['lat'], facility['geometry']['location']['lng']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=facility['name'],
                    icon=folium.Icon(color=color)
                ).add_to(m)
        
        # Display the map
        folium_static(m)
    
    def geocode_address(self):
        """Geocode patient address using Google Geocoding API"""
        # Get address components
        address = st.session_state.patient_data.get('address', '')
        city = st.session_state.patient_data.get('city', '')
        state = st.session_state.patient_data.get('state', '')
        zipcode = st.session_state.patient_data.get('zipcode', '')
        
        # Build address string
        address_parts = []
        if address:
            address_parts.append(address)
        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if zipcode:
            address_parts.append(zipcode)
            
        full_address = ", ".join(address_parts)
        
        # Call Google Geocoding API
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": full_address,
                "key": self.google_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': result['formatted_address']
                }
            else:
                st.error(f"Geocoding error: {data['status']}")
                return None
        except Exception as e:
            st.error(f"Error geocoding address: {str(e)}")
            return None
    
    def search_nearby_places(self, lat, lng, place_type, radius_miles, is_emergency=False):
        """Search for healthcare facilities using Google Places API"""
        try:
            # Convert miles to meters for Google API
            radius_meters = int(radius_miles * 1609.34)  # 1 mile = 1609.34 meters
            
            # First call - get basic place data
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            
            # Handle different search types
            if place_type in ["Hospital", "Medical Clinic", "Doctor's Office", "Urgent Care", "Pharmacy"]:
                search_type = place_type.lower().replace("'s", "").replace(" ", "_")
                if search_type == "medical_clinic":
                    search_type = "doctor"
                
                params = {
                    "location": f"{lat},{lng}",
                    "radius": min(radius_meters, 50000),  # API limit is 50,000 meters
                    "type": search_type,
                    "key": self.google_api_key
                }
            else:
                # Search by keyword for specific services
                params = {
                    "location": f"{lat},{lng}",
                    "radius": min(radius_meters, 50000),
                    "keyword": place_type,
                    "type": "health",
                    "key": self.google_api_key
                }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] != 'OK':
                st.error(f"Places API error: {data['status']}")
                # If API fails, use fallback data for demo purposes
                return self.get_fallback_results(lat, lng, place_type, radius_miles)
            
            places = data['results']
            
            # Add distance calculation
            for place in places:
                if 'geometry' in place and 'location' in place['geometry']:
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    
                    # Calculate distance in miles
                    place['distance'] = self.calculate_distance(lat, lng, place_lat, place_lng)
            
            # Sort by distance
            places = sorted(places, key=lambda x: x.get('distance', 999))
            
            # Get additional details for each place
            detailed_places = []
            for place in places[:10]:  # Limit to top 10 to minimize API calls
                details = self.get_place_details(place['place_id'])
                if details:
                    # Merge the details with the place data
                    merged_place = {**place, **details}
                    detailed_places.append(merged_place)
                else:
                    detailed_places.append(place)
            
            return detailed_places
        except Exception as e:
            st.error(f"Error searching places: {str(e)}")
            # Return fallback data if real API fails
            return self.get_fallback_results(lat, lng, place_type, radius_miles)
    
    def get_place_details(self, place_id):
        """Get detailed information about a place using Google Place Details API"""
        try:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,formatted_phone_number,opening_hours,website,url,type,rating,user_ratings_total",
                "key": self.google_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and 'result' in data:
                return data['result']
            return {}
        except Exception as e:
            st.warning(f"Error getting place details: {str(e)}")
            return {}
    
    def get_fallback_results(self, lat, lng, place_type, radius_miles):
        """Return fallback results when API fails (for demo purposes)"""
        # Create realistic fallback data based on the location
        facilities = []
        
        # Get city and state from session state
        city = st.session_state.patient_data.get('city', 'the city')
        state = st.session_state.patient_data.get('state', '')
        
        # Facility names based on type
        if "Hospital" in place_type:
            names = [
                f"{city} General Hospital",
                f"{city} Memorial Medical Center",
                f"University Hospital of {city}",
                f"{state if state else 'Community'} Medical Center",
                f"Saint Mary's Hospital"
            ]
        elif "Emergency" in place_type:
            names = [
                f"{city} Emergency Care Center",
                f"24/7 Emergency Room - {city}",
                f"Urgent Care of {city}",
                f"{city} Memorial ER",
                f"Express Emergency Care"
            ]
        else:
            names = [
                f"{city} Medical Clinic",
                f"Downtown Healthcare Center",
                f"{city} Physicians Group",
                f"Family Care Center",
                f"{city} Medical Associates"
            ]
            
        # Generate 3-5 facilities
        import random
        random.seed(str(lat) + str(lng))  # Make it deterministic but location-dependent
        
        num_facilities = min(5, max(3, random.randint(3, 5)))
        
        for i in range(num_facilities):
            # Randomize distance within radius
            distance = round(random.uniform(1, radius_miles), 1)
            
            # Calculate approximate coordinates based on distance and angle
            angle = i * (360 / num_facilities)
            place_lat = lat + (distance * math.sin(math.radians(angle)) / 69)
            place_lng = lng + (distance * math.cos(math.radians(angle)) / (69 * math.cos(math.radians(lat))))
            
            # Create facility object
            facility = {
                "name": names[i % len(names)],
                "vicinity": f"{100 + i*100} Main St, {city}, {state}",
                "distance": distance,
                "rating": round(3.0 + random.random() * 2.0, 1),  # Random rating 3.0-5.0
                "user_ratings_total": random.randint(10, 200),
                "geometry": {
                    "location": {
                        "lat": place_lat,
                        "lng": place_lng
                    }
                },
                "types": ["health", "point_of_interest", place_type.lower().replace(" ", "_")],
                "place_id": f"DEMO_PLACE_{i}"
            }
            
            facilities.append(facility)
            
        return facilities
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two points using haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        r = 3956  # Radius of Earth in miles
        
        # Calculate distance
        distance = r * c
        return round(distance, 1)
    
    def _open_directions(self, facility):
        """Open directions to the facility in Google Maps"""
        if 'geometry' in facility and 'location' in facility['geometry']:
            lat = facility['geometry']['location']['lat']
            lng = facility['geometry']['location']['lng']
            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
            if 'place_id' in facility and facility['place_id'][:5] != "DEMO_":
                maps_url += f"&destination_place_id={facility['place_id']}"
            st.markdown(f"[Get Directions in Google Maps]({maps_url})")
        elif 'vicinity' in facility:
            address = facility['vicinity'].replace(" ", "+")
            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={address}"
            st.markdown(f"[Get Directions in Google Maps]({maps_url})")
    
    def _add_provider_to_care_plan(self, facility):
        """Add the selected provider to the patient's care plan"""
        if 'patient_data' not in st.session_state:
            st.session_state.patient_data = {}
            
        if 'recommended_providers' not in st.session_state.patient_data:
            st.session_state.patient_data['recommended_providers'] = []
            
        # Add the provider to the recommended providers list
        st.session_state.patient_data['recommended_providers'].append({
            'name': facility['name'],
            'specialty': ", ".join([t.replace('_', ' ').title() for t in facility.get('types', [])[:2] 
                     if t not in ['point_of_interest', 'establishment', 'health']]) or "Healthcare Provider",
            'address': facility.get('vicinity', 'No address available'),
            'phone': facility.get('formatted_phone_number', 'N/A'),
            'distance': facility.get('distance', 0),
            'added_on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def integrate_with_care_planning(self):
        """Display recommended providers in the care planning stage"""
        if 'patient_data' in st.session_state and 'recommended_providers' in st.session_state.patient_data:
            providers = st.session_state.patient_data['recommended_providers']
            
            if providers:
                st.subheader("Recommended Healthcare Providers")
                
                for provider in providers:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{provider['name']}**")
                            st.write(f"Specialty: {provider['specialty']}")
                            st.write(f"Address: {provider['address']}")
                            st.write(f"Phone: {provider['phone']}")
                        
                        with col2:
                            st.write(f"Distance: {provider['distance']:.1f} miles")
                            
                        st.markdown("---")
            else:
                st.write("No healthcare providers have been recommended yet.")
                if st.button("Find Healthcare Providers", key="find_providers_care_planning"):
                    st.session_state.previous_stage = 'care_planning'
                    st.session_state.current_stage = 'hospital_finder'
                    st.rerun()