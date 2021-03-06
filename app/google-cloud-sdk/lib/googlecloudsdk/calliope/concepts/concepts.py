# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Classes to specify concept and resource specs.

Concept specs hold information about concepts. "Concepts" are any entity that
has multiple attributes, which can be specified via multiple flags on the
command line. A single concept spec should be created and re-used for the same
concept everywhere it appears.

Resource specs (currently the only type of concept spec used in gcloud) hold
information about a Cloud resource. "Resources" are types of concepts that
correspond to Cloud resources specified by a collection path, such as
'example.projects.shelves.books'. Their attributes correspond to the parameters
of their collection path. As with concept specs, a single resource spec
should be defined and re-used for each collection.

For resources, attributes can be configured by ResourceParameterAttributeConfigs
using kwargs. In many cases, users should also be able to reuse configs for the
same attribute across several resources (for example,
'example.projects.shelves.books.pages' could also use the shelf and project
attribute configs).
"""

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


class InitializeError(exceptions.Error):
  """Raised if a spec fails to initialize."""


class ConceptSpec(object):
  """Base class for concept args."""

  @property
  def attributes(self):
    """A list of Attribute objects representing the attributes of the concept.

    Must be defined in subclasses.
    """
    raise NotImplementedError

  @property
  def name(self):
    """The name of the overall concept.

    Must be defined in subclasses.
    """
    raise NotImplementedError

  def Initialize(self, deps):
    """Initializes the concept using information provided by a Deps object.

    Must be defined in subclasses.

    Args:
      deps: googlecloudsdk.calliope.concepts.deps.Deps object representing the
        fallthroughs for the concept's attributes.

    Returns:
      the initialized concept.

    Raises:
      InitializeError, if the concept cannot be initialized.
    """
    raise NotImplementedError


class Attribute(object):
  """An attribute of a concept.

  Attributes:
    name: The name of the attribute. Used primarily to control the arg or flag
      name corresponding to the attribute.
    help_text: String describing the attribute's relationship to the concept,
      used to generate help for an attribute flag.
    required: True if the attribute is required.
    fallthroughs: [googlecloudsdk.calliope.concepts.deps.Fallthrough], the list
      of sources of data, in priority order, that can provide a value for the
      attribute if not given on the command line. These should only be sources
      inherent to the attribute, such as associated properties, not command-
      specific sources.
  """

  def __init__(self, name, help_text=None, required=False, fallthroughs=None):
    self.name = name
    self.help_text = help_text
    self.required = required
    self.fallthroughs = fallthroughs or []

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    for attribute_name in ['name', 'help_text', 'required']:
      if (getattr(other, attribute_name, '') !=
          getattr(self, attribute_name, '')):
        return False
    return True


class ResourceSpec(ConceptSpec):
  """Defines a Cloud resource as a set of attributes for argument creation.
  """

  def __init__(self, resource_collection, resource_name=None,
               api_version=None, **kwargs):
    """Initializes a ResourceSpec.

    To use a ResourceSpec, give a collection path such as
    'cloudiot.projects.locations.registries', and optionally an
    API version.

    For each parameter in the collection path, an attribute is added to the
    resource spec. Names can be created by default or overridden in the
    attribute_configs dict, which maps from the parameter name to a
    ResourceParameterAttributeConfig object. ResourceParameterAttributeConfigs
    also contain information about the help text that describes the attribute.

    Attribute naming: By default, attributes are named after their collection
    path param names, or "name" if they are the "anchor" attribute (the final
    parameter in the path).

    Args:
      resource_collection: The collection path of the resource.
      resource_name: The name of the resource, which will be used in attribute
        help text.
      api_version: Overrides the default version in the resource
        registry.
      **kwargs: Parameter names (such as 'projectsId') from the
        collection path, mapped to ResourceParameterAttributeConfigs.
    """
    self._name = resource_name
    self.collection = resource_collection
    self._resources = resources.REGISTRY.Clone()
    self._collection_info = self._resources.GetCollectionInfo(
        resource_collection, api_version=api_version)
    collection_params = self._collection_info.GetParams('')
    self._attributes = []
    self._param_names_map = {}
    anchor = False

    # Add attributes.
    for i, param_name in enumerate(collection_params):
      if i == len(collection_params) - 1:
        anchor = True
      attribute_config = kwargs.get(param_name,
                                    ResourceParameterAttributeConfig())
      attribute_name = self._AttributeName(param_name, attribute_config,
                                           anchor=anchor)
      fallthroughs = []
      if attribute_config.prop:
        fallthroughs.append(deps_lib.PropertyFallthrough(attribute_config.prop))
      new_attribute = Attribute(
          name=attribute_name,
          help_text=attribute_config.help_text,
          required=True,
          fallthroughs=fallthroughs)
      self._attributes.append(new_attribute)
      # Keep a map from attribute names to param names. While attribute names
      # are used for error messaging and arg creation/parsing, resource parsing
      # during command runtime requires parameter names.
      self._param_names_map[new_attribute.name] = param_name

  @property
  def attributes(self):
    return self._attributes

  @property
  def name(self):
    return self._name

  @property
  def anchor(self):
    """The "anchor" attribute of the resource."""
    return self.attributes[-1]

  def _AttributeName(self, param_name, attribute_config, anchor=False):
    """Chooses attribute name for a param name.

    If attribute_config gives an attribute name, that is used. Otherwise, if the
    param is an anchor attribute, 'name' is used, or if not, param_name is used.

    Args:
      param_name: str, the parameter name from the collection.
      attribute_config: ResourceParameterAttributeConfig, the config for the
        param_name.
      anchor: bool, whether the parameter is the "anchor" or the last in the
        collection path.

    Returns:
      (str) the attribute name.
    """
    if attribute_config.attribute_name:
      return attribute_config.attribute_name
    if anchor:
      return 'name'
    else:
      return param_name

  def _ParamName(self, attribute_name):
    """Given an attribute name, gets the param name for resource parsing."""
    return self._param_names_map.get(attribute_name, '')

  def Initialize(self, deps):
    """Initializes a resource given its fallthroughs.

    If the attributes have a property or arg fallthrough but the full
    resource name is provided to the anchor attribute flag, the information
    from the resource name is used over the properties and args. This
    preserves typical resource parsing behavior in existing surfaces.

    Args:
      deps: googlecloudsdk.calliope.concepts.deps.Deps object used to represent
        fallthroughs.

    Returns:
      (googlecloudsdk.core.resources.Resource) the fully initialized resource.

    Raises:
      googlecloudsdk.calliope.concepts.concepts.InitializeError, if the concept
        can't be initialized.
    """
    params = {}
    def LazyGet(name):
      return lambda: deps.Get(name)
    for attribute in self.attributes:
      params[self._ParamName(attribute.name)] = LazyGet(attribute.name)
    self._resources.RegisterApiByName(self._collection_info.api_name,
                                      self._collection_info.api_version)
    try:
      return self._resources.Parse(
          deps.Get(self.anchor.name),
          collection=self.collection,
          params=params)
    except deps_lib.AttributeNotFoundError as e:
      raise InitializeError(
          'The [{}] resource is not properly specified.\n'
          '{}'.format(self.name, e.message))


class ResourceParameterAttributeConfig(object):
  """Configuration used to create attributes from resource parameters."""

  def __init__(self, name=None, help_text=None, prop=None):
    """Create a resource attribute.

    Args:
      name: str, the name of the attribute. This controls the naming of flags
        based on the attribute.
      help_text: str, generic help text for any flag based on the attribute.
      prop: core.properties._Property, the property object to read as a
        fallthrough for the attribute.
    """
    self.attribute_name = name
    self.help_text = help_text
    self.prop = prop
