"""Load the standalone Webasto IR codec into ESPHome builds."""

import esphome.codegen as cg
import esphome.config_validation as cv

CODEOWNERS = ["@gszigethy"]
CONFIG_SCHEMA = cv.Schema({})


async def to_code(config) -> None:
    cg.add_global(
        cg.RawStatement('#include "esphome/components/webasto_ir/webasto_ir.h"')
    )
