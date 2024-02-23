#include "contiki.h"
#include "coap-engine.h"
#include "sys/log.h"
#include "os/lib/json/jsonparse.h"

#define LOG_MODULE "Ventilation Resource"
#define LOG_LEVEL LOG_LEVEL_INFO

/* ------------------------------- */

static enum VENTILATION_LEVEL { OFF = 1, LOW, MEDIUM, HIGH } current_ventilation_level = OFF;

int set_ventilation(int requested_ventilation_level) 
{  
    if (requested_ventilation_level != current_ventilation_level) {
        if (requested_ventilation_level == OFF) {
            LOG_INFO("Ventilation actuator turned off");
            LOG_INFO_("\n");
        } else if (requested_ventilation_level == LOW) {
            LOG_INFO("Ventilation actuator set to low mode");
            LOG_INFO_("\n");
        } else if (requested_ventilation_level == MEDIUM) {
            LOG_INFO("Ventilation actuator set to medium mode");
            LOG_INFO_("\n");
        } else if (requested_ventilation_level == HIGH) {
            LOG_INFO("Ventilation actuator set to high mode");
            LOG_INFO_("\n");
        } else {
            LOG_ERR("Requested invalid ventilation mode");
            LOG_ERR_("\n");
            return 0;
        }
        current_ventilation_level = requested_ventilation_level;
    } else {
        LOG_INFO("Ventilation actuator is already in state %d", current_ventilation_level);
        LOG_INFO_("\n");
    }
    return 1;
}

/* ------------------------------- */

static void res_put_handler(coap_message_t *request, coap_message_t *response, uint8_t *bres_put_handleruffer, uint16_t preferred_size, int32_t *offset);

RESOURCE(res_ventilation, "title=\"VENTILATION\";rt=\"Control\"", NULL, NULL, res_put_handler, NULL);

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
        static int requested_ventilation_level;
        static int ventilation_level_found = 0;

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
            if (jsonparse_strcmp_value(&js, "v") == 0) {
                json_element = jsonparse_next(&js);
                requested_ventilation_level = jsonparse_get_value_as_int(&js);
                ventilation_level_found = 1;
                LOG_INFO("Requested ventilation level: %d", requested_ventilation_level);
                LOG_INFO_("\n");
                break;
            } else {
                ventilation_level_found = 0;
            }
        }

        if (!ventilation_level_found) {
            coap_set_status_code(response, BAD_REQUEST_4_00);
            coap_set_header_content_format(response, APPLICATION_JSON);
            snprintf((char *)buffer, COAP_MAX_CHUNK_SIZE, "{\"msg\":\"Missing ventilation level\"}");
            coap_set_payload(response, buffer, strlen((char *)buffer));
        } else if (set_ventilation(requested_ventilation_level)) {
            coap_set_status_code(response, CONTENT_2_05);
        } else {
            coap_set_status_code(response, NOT_ACCEPTABLE_4_06);
            coap_set_header_content_format(response, APPLICATION_JSON);
            snprintf((char *)buffer, COAP_MAX_CHUNK_SIZE, "{\"msg\":\"Requested invalid ventilation level\"}");
            coap_set_payload(response, buffer, strlen((char *)buffer));
        }
    }
}