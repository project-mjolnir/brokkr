"""
Build pipelines to be executed by a MultiprocessHandler.
"""

# Standard library imports
import copy
import importlib
import logging

# Local imports
import brokkr.utils.misc


INTERVAL_DEFAULT = 60

PRESET_KEY = "_preset"

LOGGER = logging.getLogger(__name__)


class Builder(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            subobjects=None,
            name=None,
            name_sep=":",
            exit_event=None,
            subobject_lookup=None,
            subobject_presets=None,
                ):
        self.subobjects = [] if subobjects is None else subobjects
        self.name = "Unnamed" if name is None else name
        self.name_sep = name_sep
        self.exit_event = exit_event
        self.subobject_lookup = (
            {} if subobject_lookup is None else subobject_lookup)
        self.subobject_presets = (
            {} if subobject_presets is None else subobject_presets)

    def build_subobject(
            self,
            subobject,
            idx=0,
            exit_event=None,
            subobject_lookup=None,
            subobject_presets=None,
                ):
        if exit_event is None:
            exit_event = self.exit_event
        if subobject_lookup is None:
            subobject_lookup = self.subobject_lookup
        if subobject_presets is None:
            subobject_presets = self.subobject_presets

        if not isinstance(subobject, Builder):
            # Lookup subobject names in the local dictionary
            if isinstance(subobject, str):
                try:
                    subobject = subobject_lookup[subobject]
                except KeyError:
                    # If subobject not found, format it as a preset
                    subobject = {PRESET_KEY: subobject}
            # Lookup subobject names in the preset dictionary
            if subobject.get(PRESET_KEY, None) is not None:
                key_parts = subobject[PRESET_KEY].split(".")
                try:
                    preset = brokkr.utils.misc.get_inner_dict(
                        obj=subobject_presets, keys=key_parts)
                except KeyError as e:
                    LOGGER.error(
                        "%s finding object %s of preset %r in of pipeline %r",
                        type(e).__name__, e, subobject[PRESET_KEY], self.name)
                    LOGGER.info("Error details:", exc_info=True)
                    sub_dict = subobject_presets
                    LOGGER.info("Valid names for local lookup table: %r",
                                list(subobject_lookup.keys()))
                    for key_part, next_part in zip(["root", *key_parts[:-1]],
                                                   key_parts):
                        LOGGER.info("Valid names for preset level %r: %r",
                                    key_part, list(sub_dict.keys()))
                        sub_dict = sub_dict.get(next_part, None)
                        if sub_dict is None:
                            break
                    raise SystemExit(1)
                del subobject[PRESET_KEY]
                subobject = {**preset, **subobject}

            if subobject.get("name", None) is None:
                subobject["name"] = f"{self.name}{self.name_sep}{idx + 1}"
            try:
                builder = BUILDERS[subobject.get("_builder", "")]
            except KeyError as e:
                LOGGER.error(
                    "%s finding builder %s for subobject %s of pipeline %s",
                    type(e).__name__, e, subobject.get("name", "Unnamed"),
                    self.name)
                LOGGER.info("Error details:", exc_info=True)
                LOGGER.info("Valid builders: %r", BUILDERS)
                raise SystemExit(1)

            subobject.pop("_builder", None)
            subobject = builder(
                exit_event=exit_event,
                subobject_lookup=subobject_lookup,
                subobject_presets=subobject_presets,
                **subobject)
        return subobject

    def build_subobjects(self, **build_kwargs):
        # Recursively build the sub-objects comprising this object
        if self.subobjects is not None:
            built_subobjects = []
            try:
                subobjects = self.subobjects.values()
            except AttributeError:  # For lists that don't have values()
                subobjects = self.subobjects
            for idx, subobject in enumerate(subobjects):
                built_subobject = self.build_subobject(
                    subobject, idx=idx, **build_kwargs)
                built_subobjects.append(built_subobject)
            return built_subobjects
        return None

    def build(self, exit_event=None, **build_kwargs):
        return self.build_subobjects(exit_event=exit_event, **build_kwargs)


class ObjectBuilder(Builder):
    def __init__(
            self,
            _module_path="brokkr.pipeline.pipeline",
            _class_name="SequentialPipeline",
            name=None,
            steps=None,
            exit_event=None,
            subobject_lookup=None,
            subobject_presets=None,
            **init_kwargs):
        self.module_path = _module_path
        self.class_name = _class_name

        self.init_kwargs = copy.deepcopy(init_kwargs)
        if name is not None:
            self.init_kwargs["name"] = name

        if name is None:
            name = "Unnamed " + self.class_name
        super().__init__(
            subobjects=steps,
            name=name,
            exit_event=exit_event,
            subobject_lookup=subobject_lookup,
            subobject_presets=subobject_presets,
            )

    def build_subobject(
            self,
            subobject,
            idx=0,
            exit_event=None,
            subobject_lookup=None,
            subobject_presets=None,
                ):
        subobject = super().build_subobject(
            subobject,
            idx=idx,
            exit_event=exit_event,
            subobject_lookup=subobject_lookup,
            subobject_presets=subobject_presets,
            )

        built_subobject = subobject.build(
            exit_event=exit_event,
            subobject_lookup=subobject_lookup,
            subobject_presets=subobject_presets,
            )
        return built_subobject

    def build(self, exit_event=None, **build_kwargs):
        LOGGER.debug(
            "Building %s (%s.%s) with kwargs %r",
            self.name, self.module_path, self.class_name, self.init_kwargs)

        # Recursively build the steps comprising this item, if present
        built_steps = super().build(exit_event=exit_event, **build_kwargs)
        if built_steps:
            self.init_kwargs["steps"] = built_steps

        # Load and generate the final object
        module_object = importlib.import_module(self.module_path)
        obj_class = getattr(module_object, self.class_name)
        obj_instance = obj_class(exit_event=exit_event, **self.init_kwargs)
        return obj_instance


class MonitorBuilder(ObjectBuilder):
    def __init__(
            self,
            monitor_input_steps,
            monitor_output_steps=None,
            monitor_interval_s=INTERVAL_DEFAULT,
            name="Monitoring Data Pipeline",
            **builder_kwargs,
                ):
        monitor_input_step = {
            "_module_path": "brokkr.pipeline.step",
            "_class_name": "SequentialMultiStep",
            "name": "Monitoring Data Input",
            "steps": monitor_input_steps,
            }

        if monitor_output_steps is None:
            monitor_output_step = {
                "_module_path": "brokkr.outputs.print",
                "_class_name": "PrettyPrintOutput",
                "name": "Monitoring Data Print Output",
                }
        else:
            monitor_output_step = {
                "_module_path": "brokkr.pipeline.step",
                "_class_name": "SequentialMultiStep",
                "name": "Monitoring Data Output",
                "steps": monitor_output_steps,
                }

        monitor_steps = [monitor_input_step, monitor_output_step]
        monitor_pipeline = {
            "name": name,
            "period_s": monitor_interval_s,
            "steps": monitor_steps,
            }

        super().__init__(**monitor_pipeline, **builder_kwargs)


class TopLevelBuilder(Builder):
    def __init__(self, pipelines, name="Pipeline", **builder_kwargs):
        super().__init__(
            subobjects=pipelines,
            name=name,
            name_sep="-",
            **builder_kwargs,
            )
        print(pipelines)


BUILDERS = {
    "": ObjectBuilder,
    "object": ObjectBuilder,
    "monitor": MonitorBuilder,
    "toplevel": TopLevelBuilder,
    }
