CONTIKI_PROJECT = mqtt-sensor
all: $(CONTIKI_PROJECT)

CONTIKI = ../../../..

include $(CONTIKI)/Makefile.dir-variables
MODULES += $(CONTIKI_NG_APP_LAYER_DIR)/mqtt

MODULES_REL += arch/platform/$(TARGET)

ifeq ($(DEFINES), TEMPERATURE_HUMIDITY_CO2)
MODULES_REL += ./resources
MODULES += $(CONTIKI_NG_APP_LAYER_DIR)/coap
MODULES += $(CONTIKI_NG_LIB_DIR)/json
endif

-include $(CONTIKI)/Makefile.identify-target

include $(CONTIKI)/Makefile.include