#ifndef __COAP_PROTOCOL_H__
#define __COAP_PROTOCOL_H__

#define SERVER_ENDPOINT "coap://[fd00::1]:5683"
#define BUFFER_SIZE		100

static void set_state(enum node_state new_state);

#ifdef TEMPERATURE
int set_temperature(int requested_temperature);
#elif defined(VENTILATION)
int set_ventilation(int requested_ventilation_level);
#endif

static coap_endpoint_t server_endpoint;
static coap_message_t request[1];
static char registration_resource_url[] = "/registration";
static char keeaplive_resource_url[] = "/keepalive";
static char buffer[BUFFER_SIZE];

void client_chunk_handler(coap_message_t *response)
{
	// CoAP request timed out
	if (response == NULL) {
		LOG_ERR("CoAP request timed out");
		LOG_ERR_("\n");

		// Turn off actuator if keepalive request timed out
		if (current_state == CONNECTED) {
#ifdef TEMPERATURE
			set_temperature(1);
#elif defined(VENTILATION)
			set_ventilation(1);
#endif
		}
		
		set_state(NOT_CONNECTED);
		return;
	}

	// Check request status code
	if (response->code == CREATED_2_01 || response->code == CHANGED_2_04) {
		LOG_INFO("CoAP request received successfully");
		LOG_INFO_("\n");
		set_state(CONNECTED);

		// Schedule keepalive timer
		etimer_set(&keepalive_timer, actuator_info.keepalive * CLOCK_SECOND);
	} else {
		LOG_ERR("CoAP server error code: %s", response->code == INTERNAL_SERVER_ERROR_5_00 ? "500" : "404");
		LOG_ERR_("\n");
		set_state(NOT_CONNECTED);
	} 
}

static void set_coap_registration_message()
{
	// Setup CoAP message header
	coap_endpoint_parse(SERVER_ENDPOINT, strlen(SERVER_ENDPOINT), &server_endpoint);
	coap_init_message(request, COAP_TYPE_CON, COAP_POST, 0);
	coap_set_header_uri_path(request, registration_resource_url);

	// Add node information into payload
	serialize_actuator_info(buffer, BUFFER_SIZE);
	coap_set_payload(request, (uint8_t *)buffer, strlen(buffer));
}

static void set_coap_keepalive_message()
{
	// Setup CoAP message header
	coap_endpoint_parse(SERVER_ENDPOINT, strlen(SERVER_ENDPOINT), &server_endpoint);
	coap_init_message(request, COAP_TYPE_CON, COAP_POST, 0);
	coap_set_header_uri_path(request, keeaplive_resource_url);

	// Add node information into payload
	serialize_keepalive(buffer, BUFFER_SIZE);
	coap_set_payload(request, (uint8_t *)buffer, strlen(buffer));
}

#endif