"""
Build pipelines to be executed by a MultiprocessHandler.
"""

# Standard library imports
import copy
import importlib
import logging

# Local imports
import brokkr.utils.misc


MONITOR_INTERVAL_DEFAULT = 60

LOGGER = logging.getLogger(__name__)


class Builder(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            subobjects=None,
            subobject_builder=None,
            name=None,
            name_sep=":",
            exit_event=None,
                ):
        self.subobjects = [] if subobjects is None else subobjects
        self.subobject_builder = (type(self) if subobject_builder is None
                                  else subobject_builder)
        self.name = "Unnamed" if name is None else name
        self.name_sep = name_sep
        self.exit_event = exit_event

    def build_subobject(self, subobject, idx=0, exit_event=None):
        if exit_event is None:
            exit_event = self.exit_event
        if not isinstance(subobject, Builder):
            if subobject.get("name", None) is None:
                subobject["name"] = f"{self.name}{self.name_sep}{idx + 1}"
            subobject = self.subobject_builder(**subobject)
        built_subobject = subobject.build(exit_event=exit_event)
        return built_subobject

    def build_subobjects(self, exit_event=None):
        if exit_event is None:
            exit_event = self.exit_event
        # Recursively build the sub-objects comprising this object
        if self.subobjects is not None:
            built_subobjects = []
            for idx, subobject in enumerate(self.subobjects):
                built_subobject = self.build_subobject(
                    subobject, idx=idx, exit_event=exit_event)
                built_subobjects.append(built_subobject)
            return built_subobjects
        return None

    def build(self, exit_event=None):
        if exit_event is None:
            exit_event = self.exit_event
        return self.build_subobjects(exit_event=exit_event)


class ObjectBuilder(Builder):
    def __init__(
            self,
            _module_path="brokkr.pipeline.pipeline",
            _class_name="SequentialPipeline",
            _subobject_builder=None,
            name=None,
            steps=None,
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
            subobject_builder=_subobject_builder,
            name=name,
            )

    def build(self, exit_event=None):
        LOGGER.debug(
            "Building %s (%s.%s) with kwargs %r",
            self.name, self.module_path, self.class_name, self.init_kwargs)

        # Recursively build the steps comprising this item, if present
        built_steps = super().build(exit_event=exit_event)
        if built_steps:
            self.init_kwargs["steps"] = built_steps

        # Load and generate the final object
        module_object = importlib.import_module(self.module_path)
        obj_class = getattr(module_object, self.class_name)
        obj_instance = obj_class(exit_event=exit_event, **self.init_kwargs)
        return obj_instance


class TopLevelBuilder(Builder):
    def __init__(self, pipelines, name="Pipeline"):
        super().__init__(
            subobjects=pipelines,
            subobject_builder=ObjectBuilder,
            name=name,
            name_sep="-",
            )


class MonitorBuilder(ObjectBuilder):
    def __init__(
            self,
            monitor_input_steps,
            monitor_output_steps=None,
            interval_s=MONITOR_INTERVAL_DEFAULT,
            name="Monitoring Pipeline",
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
            "period_s": interval_s,
            "steps": monitor_steps,
            }

        super().__init__(
            _subobject_builder=ObjectBuilder,
            **monitor_pipeline)
