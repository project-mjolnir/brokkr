"""
Build pipelines to be executed by a MultiprocessHandler.
"""

# Standard library imports
import copy
import importlib
import importlib.util
import logging

# Local imports
import brokkr.utils.misc


INTERVAL_DEFAULT = 60

PRESET_KEY = "_preset"

PLUGIN_SUBPACKAGE = "plugins"
PLUGIN_SUFFIX_DEFAULT = ".py"

LOGGER = logging.getLogger(__name__)


class BuildContext(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            exit_event=None,
            subobject_lookup=None,
            subobject_presets=None,
            plugin_root_path=None,
            na_marker=None,
            preset_fill_mappings=None,
                ):
        self.exit_event = exit_event
        self.subobject_lookup = (
            {} if subobject_lookup is None else subobject_lookup)
        self.subobject_presets = (
            {} if subobject_presets is None else subobject_presets)
        if plugin_root_path is None:
            self.plugin_root_path = None
        else:
            self.plugin_root_path = brokkr.utils.misc.convert_path(
                plugin_root_path)
        self.na_marker = na_marker
        self.preset_fill_mappings = (
            [] if preset_fill_mappings is None else preset_fill_mappings)

    def merge(self, build_context):
        if build_context is None:
            return self
        build_context_kwargs = {
            key: value for key, value in vars(build_context).items() if value}
        build_context = BuildContext(**{**vars(self), **build_context_kwargs})
        return build_context


class Builder(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            subobjects=None,
            name=None,
            name_sep=":",
            build_context=None,
                ):
        self.subobjects = [] if subobjects is None else subobjects
        self.name = "Unnamed" if name is None else name
        self.name_sep = name_sep
        self.build_context = (
            BuildContext() if build_context is None else build_context)
        self.subbuilders = []

    def _setup_preset(self, subobject, build_context, step_key=None):
        subobject = copy.deepcopy(subobject)
        key_parts = subobject[PRESET_KEY].split(".")
        try:
            preset = brokkr.utils.misc.get_inner_dict(
                obj=build_context.subobject_presets, keys=key_parts)
        except KeyError as e:
            LOGGER.error(
                "%s finding object %s of preset %r in pipeline %r",
                type(e).__name__, e, subobject[PRESET_KEY], self.name)
            LOGGER.info("Error details:", exc_info=True)
            sub_dict = build_context.subobject_presets
            LOGGER.info("Valid names for local lookup table: %r",
                        list(build_context.subobject_lookup.keys()))
            for key_part, next_part in zip(["root", *key_parts[:-1]],
                                           key_parts):
                LOGGER.info("Valid names for preset level %r: %r",
                            key_part, list(sub_dict.keys()))
                sub_dict = sub_dict.get(next_part, None)
                if sub_dict is None:
                    break
            raise SystemExit(1)

        # Fill data types defined in steps table with data type presets
        device_preset = (
            build_context.subobject_presets[key_parts[0]])
        for preset_fill_key, preset_fill_value in (
                build_context.preset_fill_mappings):
            if preset_fill_key in subobject:
                # Build preset lookup from values in preset, config and step
                preset_fill_lookup = brokkr.utils.misc.update_dict_recursive(
                    device_preset.get(preset_fill_key, {}),
                    preset_fill_value)

                preset_filled = {}
                preset = copy.deepcopy(preset)
                for inner_key in subobject[preset_fill_key]:
                    if isinstance(inner_key, str):
                        try:
                            preset_filled[inner_key] = (
                                preset_fill_lookup[inner_key])
                        except KeyError as e:
                            LOGGER.error(
                                "%s inserting value for preset %r: "
                                "Can't find inner key %s in key %r to insert "
                                "into step %s",
                                type(e).__name__, subobject[PRESET_KEY], e,
                                preset_fill_key, step_key)
                            LOGGER.info("Error details:", exc_info=True)
                            LOGGER.info("Possible keys: %r",
                                        list(preset_fill_lookup.keys()))
                            raise SystemExit(1)
                        else:
                            preset.pop(preset_fill_key, None)
                    else:
                        preset_filled[inner_key.name] = inner_key
                subobject[preset_fill_key] = preset_filled

        # Update subobject arguments with those from preset
        del subobject[PRESET_KEY]
        subobject = brokkr.utils.misc.update_dict_recursive(
            preset, subobject)
        return subobject

    def setup_subobject(
            self,
            subobject,
            idx=0,
            build_context=None,
                ):
        build_context = self.build_context.merge(build_context)

        if not isinstance(subobject, Builder):
            # Lookup subobject names in the local dictionary
            if isinstance(subobject, str):
                step_key = subobject
                try:
                    subobject = build_context.subobject_lookup[subobject]
                except KeyError:
                    # If subobject not found, format it as a preset
                    subobject = {PRESET_KEY: subobject}
            else:
                step_key = None

            # Lookup subobject names in the preset dictionary
            if PRESET_KEY in subobject:
                subobject = self._setup_preset(
                    subobject, build_context=build_context, step_key=step_key)

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
            subobject = builder(build_context=build_context, **subobject)
        return subobject

    def setup_subobjects(self, **setup_kwargs):
        # Recursively build the sub-objects comprising this object
        if self.subobjects is not None:
            subobjects_to_setup = []
            try:
                subobjects = self.subobjects.values()
            except AttributeError:  # For lists that don't have values()
                subobjects = self.subobjects
            for idx, subobject in enumerate(subobjects):
                setup_subobject = self.setup_subobject(
                    subobject, idx=idx, **setup_kwargs)
                subobjects_to_setup.append(setup_subobject)
            return subobjects_to_setup
        return None

    def setup(self, build_context=None, **setup_kwargs):
        subbuilders = self.setup_subobjects(
            build_context=build_context, **setup_kwargs)
        if subbuilders:
            self.subbuilders = subbuilders
        return subbuilders


class ObjectBuilder(Builder):
    def __init__(
            self,
            _module_path="brokkr.pipeline.pipeline",
            _class_name="SequentialPipeline",
            _is_plugin=False,
            _dependencies=None,
            name=None,
            steps=None,
            build_context=None,
            **init_kwargs):
        self.module_path = _module_path
        self.class_name = _class_name
        self.is_plugin = _is_plugin
        self.dependencies = _dependencies

        self.init_kwargs = copy.deepcopy(init_kwargs)
        if name is not None:
            self.init_kwargs["name"] = name
        else:
            name = "Unnamed " + self.class_name

        super().__init__(
            subobjects=steps,
            name=name,
            build_context=build_context,
            )

    def setup_subobject(
            self,
            subobject,
            idx=0,
            build_context=None,
                ):
        subobject = super().setup_subobject(
            subobject,
            idx=idx,
            build_context=build_context,
            )

        subobject.setup(build_context=build_context)
        return subobject

    def build(self, build_context=None):
        LOGGER.debug(
            "Building %s (%s.%s) with kwargs %r",
            self.name, self.module_path, self.class_name, self.init_kwargs)
        build_context = self.build_context.merge(build_context)

        # Recursively build subobjects
        built_steps = [subbuilder.build() for subbuilder in self.subbuilders]
        if built_steps:
            self.init_kwargs["steps"] = built_steps

        # Load specified module or plugin
        if self.is_plugin:
            module_path = brokkr.utils.misc.convert_path(self.module_path)
            if not module_path.is_absolute():
                module_path = build_context.plugin_root_path / module_path
            if not module_path.suffix:
                module_path = module_path.with_suffix(PLUGIN_SUFFIX_DEFAULT)
            module_spec = importlib.util.spec_from_file_location(
                ".".join([PLUGIN_SUBPACKAGE, module_path.stem]), module_path)
            module_object = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module_object)
        else:
            module_object = importlib.import_module(self.module_path)

        # Build the final object
        obj_class = getattr(module_object, self.class_name)
        if (issubclass(obj_class, brokkr.pipeline.baseinput.ValueInputStep)
                and getattr(self.init_kwargs, "na_marker", None) is None):
            self.init_kwargs["na_marker"] = build_context.na_marker
        obj_instance = obj_class(
            exit_event=build_context.exit_event, **self.init_kwargs)

        return obj_instance

    def setup_and_build(self, build_context=None, **setup_kwargs):
        self.setup(build_context=build_context, **setup_kwargs)
        built_object = self.build(build_context=build_context)
        return built_object


class MonitorBuilder(ObjectBuilder):
    def __init__(
            self,
            monitor_input_steps,
            monitor_process_steps=None,
            monitor_output_steps=None,
            monitor_interval_s=INTERVAL_DEFAULT,
            name="Monitoring Data Pipeline",
            **builder_kwargs,
                ):
        if monitor_process_steps is None:
            monitor_process_steps = []

        monitor_input_step = {
            "_module_path": "brokkr.pipeline.multistep",
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
                "_module_path": "brokkr.pipeline.multistep",
                "_class_name": "SequentialMultiStep",
                "name": "Monitoring Data Output",
                "steps": monitor_output_steps,
                }

        monitor_steps = [
            monitor_input_step, *monitor_process_steps, monitor_output_step]
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


BUILDERS = {
    "": ObjectBuilder,
    "object": ObjectBuilder,
    "monitor": MonitorBuilder,
    "toplevel": TopLevelBuilder,
    }
