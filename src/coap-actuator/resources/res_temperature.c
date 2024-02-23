#include "contiki.h"
#include "coap-engine.h"
#include "sys/log.h"
#include "os/lib/json/jsonparse.h"

#define LOG_MODULE "Temperature Resource"
#define LOG_LEVEL LOG_LEVEL_INFO

/* ------------------------------- */

#define TURN_OFF            1
#define MIN_TEMPERATURE     15
#define MAX_TEMPERATURE     30

static int current_temperature = 1;

int set_temperature(int requested_temperature) 
{  
    if (requested_temperature != current_temperature) {
        if (requested_temperature == TURN_OFF) {
            LOG_INFO("Temperature actuator turned off");
            LOG_INFO_("\n");
        } else if (requested_temperature >= MIN_TEMPERATURE && requested_temperature <= MAX_TEMPERATURE){
            LOG_INFO("Temperature actuator turned on with a target of %d°C", requested_temperature);
            LOG_INFO_("\n");
        } else {
            LOG_ERR("Requested invalid temperature");
            LOG_ERR_("\n");  
            return 0; 
        }
        current_temperature = requested_temperature;
    } else {
        LOG_INFO("Temperature actuator is already set to %d", current_temperature);
        LOG_INFO_("\n");
    }
    return 1;
}

/* ------------------------------- */

static void res_put_handler(coap_message_t *request, coap_message_t *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset);

RESOURCE(res_temperature, "title=\"TEMPERATURE\";rt=\"Control\"", NULL, NULL, res_put_handler, NULL);

static void res_put_handler(coap_message_t *request, coap_message_t *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset)
{
    const char* parameters = NULL;
    int len = coap_get_payload(request, (const uint8_t**)&parameters);

    if (len <= 0) {
        coap_set_status_code(response, BAD_REQUEST_4_00);
        coap_set_header_content_format(response, APPLICATION_JSON);
        snprintf((char *)buffer, COAP_MAX_CHUNK_SIZE, "{\"msg\":\"Empty PUT payload\"}");
        coap_set_payload(response, buffer, strlen((char *)buffer));
    } else {
        static struct jsonparse_state js;
        static int requested_temperature;
        static int temperature_found = 0;

        LOG_INFO("PUT payload received: %s", parameters);
        LOG_INFO_("\n");

        // Initialiaze JSON parser
        jsonparse_setup(&js, parameters, len);

        // Iterate until JSON ends
        for (int json_element = 0; json_element != '}'; json_element = jsonparse_next(&js)) {
            // Find the next Key-Value pair
            do {
                json_element = jsonparse_next(&js);
            } while(json_element != JSON_TYPE_PAIR_NAME && json_element != '}');
                
            // Check if JSON object is ended
            if (json_element == '}')
                break;        

            // Read the parameter value
            if (jsonparse_strcmp_value(&js, "t") == 0) {
                json_element = jsonparse_next(&js);
                requested_temperature = jsonparse_get_value_as_int(&js);
                temperature_found = 1;
                LOG_INFO("Requested temperature: %d", requested_temperature);
                LOG_INFO_("\n");
                break;
            } else {
                temperature_found = 0;
            }
        }

        if (!temperature_found) {
            coap_set_status_code(response, BAD_REQUEST_4_00);
            coap_set_header_content_format(response, APPLICATION_JSON);
            snprintf((char *)buffer, COAP_MAX_CHUNK_SIZE, "{\"msg\":\"Missing temperature\"}");
            coap_set_payload(response, buffer, strlen((char *)buffer));
        } else if (set_temperature(requested_temperature)) {
            coap_set_status_code(response, CONTENT_2_05);
        } else {
            coap_set_status_code(response, NOT_ACCEPTABLE_4_06);
            coap_set_header_content_format(response, APPLICATION_JSON);
            snprintf((char *)buffer, COAP_MAX_CHUNK_SIZE, "{\"msg\":\"Requested invalid temperature\"}");
            coap_set_payload(response, buffer, strlen((char *)buffer));
        }
    }
}