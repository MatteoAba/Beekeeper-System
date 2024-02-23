#include "contiki.h"
#include "coap-engine.h"
#include "coap-blocking-api.h"
#include "coap-log.h"
#include "stdio.h"
#include "sys/etimer.h"
#include "os/dev/leds.h"
#include "os/dev/button-hal.h"
#include "sys/log.h"

#include "net/ipv6/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ipv6/uip-debug.h"
#include "net/ipv6/uiplib.h"

#define LOG_MODULE "CoAP Actuator"
#define LOG_LEVEL LOG_LEVEL_INFO

#define BUTTON_PRESS_THRESHOLD 		3
#define TEST_CONNECTIVITY_PERIOD 	(10 * CLOCK_SECOND)
#define CONFIGURATION_DELAY			(10 * CLOCK_SECOND)

/* -------------------------- */

static enum node_state { NOT_CONNECTED, CONNECTING, CONNECTED } current_state;
static uint8_t elapsed_seconds_from_press = 0;

static struct etimer test_connectivity_timer;
static struct etimer configuration_timer;
static struct etimer keepalive_timer;
static struct ctimer blinking_timer;
static uint8_t blinking_frequency = 2;

/* -------------------------- */

PROCESS(coap_actuator, "CoAP Actuator");
AUTOSTART_PROCESSES(&coap_actuator);

#include "coap-actuator.h"
#include "coap-protocol.h"

static void led_blinking_callback(void *ptr) 
{
	if (current_state == CONNECTING) {
		leds_toggle(LEDS_NUM_TO_MASK(LEDS_RED));
		ctimer_reset(&blinking_timer);
	}
}

static void set_state(enum node_state new_state) 
{
	current_state = new_state;

	switch (new_state) {
		case NOT_CONNECTED: 
			leds_on(LEDS_NUM_TO_MASK(LEDS_RED));
			break;
		case CONNECTING:
			ctimer_set(&blinking_timer, CLOCK_SECOND/blinking_frequency, led_blinking_callback, NULL);
			break;
		case CONNECTED:
			leds_off(LEDS_NUM_TO_MASK(LEDS_RED));
			break;
	}
}

PROCESS_THREAD(coap_actuator, ev, data)
{
	PROCESS_BEGIN();

	node_info_initialization();
	actuator_info.keepalive = keepalive_periods[current_keepalive];

#ifdef TEMPERATURE
	coap_activate_resource(&res_temperature, "temperature");
#elif defined(VENTILATION)
	coap_activate_resource(&res_ventilation, "ventilation");
#endif

	set_state(CONNECTING);
	etimer_set(&test_connectivity_timer, TEST_CONNECTIVITY_PERIOD);

	while(1) {
		PROCESS_WAIT_EVENT_UNTIL(ev == button_hal_periodic_event || ev == button_hal_release_event || (ev == PROCESS_EVENT_TIMER && (data == &test_connectivity_timer || data == &configuration_timer || data == &keepalive_timer)));
		
		// Button release handling
		if (ev == button_hal_release_event) {
			if (elapsed_seconds_from_press < BUTTON_PRESS_THRESHOLD) {
				// Stop existing keepalive timer
				if (etimer_expired(&keepalive_timer) == 0)
					etimer_stop(&keepalive_timer);

				// Change keepalive setting
				current_keepalive = (current_keepalive + 1) % keepalive_periods_length;
				actuator_info.keepalive = keepalive_periods[current_keepalive]; 
				LOG_INFO("Selected keepalive period: %d", actuator_info.keepalive);
				LOG_INFO_("\n");

				// Send the new configuration with a delay if the node is connected to the CoAP server
				if (current_state == CONNECTED) {
					// Start or reset the configuration timer
					if (etimer_expired(&configuration_timer) == 0)
						etimer_stop(&configuration_timer);
					etimer_set(&configuration_timer, CONFIGURATION_DELAY);
				}
			}

			elapsed_seconds_from_press = 0;
		}

		// Button press handling
		else if (ev == button_hal_periodic_event) {
			elapsed_seconds_from_press++;

			if (elapsed_seconds_from_press >= BUTTON_PRESS_THRESHOLD && current_state == NOT_CONNECTED) {
				if (etimer_expired(&configuration_timer) == 0)
					etimer_stop(&configuration_timer);

				LOG_INFO("Retrying connection to the CoAP server");
				LOG_INFO_("\n");
				set_state(CONNECTING);
				etimer_reset(&test_connectivity_timer);
			}
		}

		// Tenative CoAP registration handling
		if (ev == PROCESS_EVENT_TIMER && data == &test_connectivity_timer) {
			// Send the registration as soon as connectivity becomes available
			if (uip_ds6_get_global(ADDR_PREFERRED) == NULL || uip_ds6_defrt_choose() == NULL) {
				LOG_ERR("Client connectivity not available");
				LOG_ERR_("\n");
				etimer_reset(&test_connectivity_timer);
			} else {
				node_ip_initilization();
				set_coap_registration_message();
				COAP_BLOCKING_REQUEST(&server_endpoint, request, client_chunk_handler);
			}
		}

		// Notify node configuration
		else if (ev == PROCESS_EVENT_TIMER && data == &configuration_timer) {
			set_coap_registration_message();
			COAP_BLOCKING_REQUEST(&server_endpoint, request, client_chunk_handler);
		}

		// Send keepalive to the CoAP server
		else if (ev == PROCESS_EVENT_TIMER && data == &keepalive_timer) {
			set_coap_keepalive_message();
			COAP_BLOCKING_REQUEST(&server_endpoint, request, client_chunk_handler);
		}
	}

	PROCESS_END();
}