#include "contiki.h"
#include "coap-engine.h"
#include "sys/log.h"
#include "os/lib/json/jsonparse.h"

#define LOG_MODULE "Test Resource"
#define LOG_LEVEL LOG_LEVEL_INFO

extern uint8_t temperature_target;
extern uint8_t humidity_target;
extern uint16_t co2_target;

static void res_put_handler(coap_message_t *request, coap_message_t *response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset);

RESOURCE(res_test, "title=\"TEST\";rt=\"Control\"", NULL, NULL, res_put_handler, NULL);

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
        static int value_found = 0;

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
                temperature_target = jsonparse_get_value_as_int(&js);
                value_found = 1;
            } else if (jsonparse_strcmp_value(&js, "h") == 0) {
                json_element = jsonparse_next(&js);
                humidity_target = jsonparse_get_value_as_int(&js);
                value_found = 1;
            } else if (jsonparse_strcmp_value(&js, "c") == 0) {
                json_element = jsonparse_next(&js);
                co2_target = jsonparse_get_value_as_int(&js);
                value_found = 1;
            }
        }

        if (!value_found) {
            coap_set_status_code(response, BAD_REQUEST_4_00);
            coap_set_header_content_format(response, APPLICATION_JSON);
            snprintf((char *)buffer, COAP_MAX_CHUNK_SIZE, "{\"msg\":\"Missing values\"}");
            coap_set_payload(response, buffer, strlen((char *)buffer));
        } else {
            LOG_INFO("Target temperature: %d | Target humidity: %d | Target co2: %d", temperature_target, humidity_target, co2_target);
            LOG_INFO_("\n");
            coap_set_status_code(response, CONTENT_2_05);
        }
    }
}