 Getting familiar with bpmn-js, one step at a time.

This document is a work in progress. Help us to improve it.
A Quick Introduction

bpmn-js is a BPMN 2.0 rendering toolkit and web modeler. It is written in JavaScript, embeds BPMN 2.0 diagrams into modern browsers and requires no server backend. That makes it easy to embed it into any web application.

The library is built in a way that it can be both a viewer and web modeler. Use the viewer to embed BPMN 2.0 into your applications and enrich it with your data. Use the modeler to create BPMN 2.0 diagrams inside your application.

This walkthrough will give you an introduction on how to use the library as well as some insights into its internals, i.e. the components that contribute to its highly modular and extensible structure.
Contents

    Using the Library
        Embed the Viewer (pre-packaged)
        Roll your own Modeler (via npm)
    Understanding bpmn-js Internals
        Diagram Interaction / Modeling (diagram-js)
        BPMN Meta-Model (bpmn-moddle)
        Plugging Things together (bpmn-js)
    Going Further

Using the Library

There are two approaches to use bpmn-js in your application. An all-in-one pre-packaged version of the library allows you to quickly add BPMN to any website. The npm version is more complicated to set-up but gives you access to individual library components and allows for easier extensibility.

This section gives you an overview of both approaches. We start with an introduction on how to embed the pre-packaged version of the BPMN viewer into a website. Following that, we show how to bundle bpmn-js with your application to create a web-based BPMN editor.
Embed the Pre-Packaged Viewer

The pre-packaged version of bpmn-js allows you to embed BPMN to your website with a simple script include.

Add a container element for the rendered diagram to your website and include the library into the page.

<!-- BPMN diagram container -->
<div id="canvas"></div>

<!-- replace CDN url with local bpmn-js path -->
<script src="https://unpkg.com/bpmn-js/dist/bpmn-viewer.development.js"></script>

The included script makes the viewer available via the BpmnJS variable. We may access it via JavaScript as shown below.

<script>
  // the diagram you are going to display
  const bpmnXML;

  // BpmnJS is the BPMN viewer instance
  const viewer = new BpmnJS({ container: '#canvas' });

  // import a BPMN 2.0 diagram
  try {
    // we did well!
    await viewer.importXML(bpmnXML);
    viewer.get('canvas').zoom('fit-viewport');

  } catch (err) {
    // import failed :-(
  }
</script>

The snippet uses the Viewer#importXML API to display a pre-loaded BPMN 2.0 diagram. Importing a diagram is asynchronous and, once finished, the viewer notifies us via a callback about the results.

After import, we may access various diagram services via Viewer#get. In the snippet above, we interact with the Canvas to fit the diagram to the currently available viewport size.

Often times it is more practical to load the BPMN 2.0 diagram dynamically via AJAX. This can be accomplished using plain JavaScript (as seen below) or via utility libraries such as jQuery, which provide more convenient APIs.

<script>
function fetchDiagram(url) {
  return fetch(url).then(response => response.text());
}

async function run() {
  const diagram = await fetchDiagram('path-to-diagram.bpmn');

  try {
    await viewer.importXML(diagram);
    // ...
  } catch (err) {
    // ...
  }
}

run();
</script>

Check out the pre-packaged example as well as our starter examples to learn more.
Roll Your Own Modeler

Use bpmn-js via npm if you would like to build customizations around the library. This approach has various advantages such as access to individual library components. It also gives us more control over what to package as part of the viewer / modeler. However, it requires us to bundle bpmn-js with our application using an ES module aware bundler such as Webpack.

    If you are new to the world of JavaScript bundling follow along our bundling example.

In the remainder of this section we loosely follow the modeler example to create a web-based BPMN editor.
Include the Library

First install bpmn-js via npm:

npm install bpmn-js

Then access the BPMN modeler via an ES import:

import Modeler from 'bpmn-js/lib/Modeler';

// create a modeler
const modeler = new Modeler({ container: '#canvas' });

// import diagram
try {
  await modeler.importXML(bpmnXML);
  // ...
} catch (err) {
  // err...
}

Again, this assumes you provide an element with the id canvas as part of your HTML for the modeler to render into.
Add Stylesheets

When embedding the modeler into a webpage, include the diagram-js stylesheet as well as the BPMN icon font with it. Both are shipped with the bpmn-js distribution under the dist/assets folder.

<link rel="stylesheet" href="bpmn-js/dist/assets/diagram-js.css" />
<link rel="stylesheet" href="bpmn-js/dist/assets/bpmn-font/css/bpmn.css" />

Adding the stylesheets ensures diagram elements receive proper styling as well as context pad and palette entries show BPMN symbols.
Bundle for the Browser

bpmn-js and its dependencies distribute ES modules. Use an ES module aware bundler to pack bpmn-js along with your application. Learn more by following along with the bundling example.
Hook into Life-Cycle Events

Events allow you to hook into the life-cycle of the modeler as well as diagram interaction. The following snippet shows how changed elements and modeling operations in general can be captured.

modeler.on('commandStack.changed', () => {
  // user modeled something or
  // performed an undo/redo operation
});

modeler.on('element.changed', (event) => {
  const element = event.element;

  // the element was changed by the user
});

Use Viewer#on to register for events or the EventBus inside extension modules. Stop listening for events using the Viewer#off method. Check out the interaction example to see listening for events in action.
Extend the Modeler

You may use the additionalModules option to extend the Viewer and Modeler on creation. This allows you to pass custom modules that amend or replace existing functionality.

import OriginModule from 'diagram-js-origin';

// create a modeler
const modeler = new Modeler({
  container: '#canvas',
  additionalModules: [
    OriginModule,
    require('./custom-rules'),
    require('./custom-context-pad')
  ]
});

A module (cf. Module System section) is a unit that defines one or more named services. These services configure bpmn-js or provide additional functionality, i.e. by hooking into the diagram life-cycle.

Some modules, such as diagram-js-origin or diagram-js-minimap, provide generic user interface additions. Built-in bpmn-js modules, such as bpmn rules or modeling, provide highly BPMN-specific functionality.

One common way to extend the BPMN modeler is to add custom modeling rules. In doing so, you can limit or extend the modeling operations allowed by the user.

Other examples for extensions are:

    Adding custom elements
    Custom palette / context pad
    Custom shape rendering

Check out the bpmn-js-examples project for many more toolkit extension show cases.
Build a Custom Distribution

If you would like to create your own pre-packaged version of your custom modeler or viewer, refer to the custom-bundle example. This could make sense if you carried out heavy customizations that you would like to ship to your users in simple way.
Understanding bpmn-js Internals

This section explores some bpmn-js internals.

As depicted in the architecture diagram below, bpmn-js builds on top of two important libraries: diagram-js and bpmn-moddle.
bpmn-js architecture: parts and responsibilities
bpmn-js Architecture: Parts and Responsibilities

We use diagram-js to draw shapes and connections. It provides us with ways to interact with these graphical elements as well as additional tools such as overlays that help users to build powerful BPMN viewers. For advanced use cases such as modeling it contributes the context pad, palette and facilities like redo/undo.

bpmn-moddle knows about the BPMN 2.0 meta-model defined in the BPMN 2.0 standard. It allows us to read and write BPMN 2.0 schema-compliant XML documents and access BPMN-related information behind shapes and connections drawn on the diagram.

On top of these two libraries, bpmn-js defines the BPMN specifics such as look and feel, modeling rules and tooling (i.e. palette). We will go into detail about the individual components in the following paragraphs.
Diagram Interaction / Modeling (diagram-js)

diagram-js is a toolbox for displaying and modifying diagrams on the web. It allows us to render visual elements and build interactive experiences on top of them.

It provides us with a very simple module system for building features and dependency injection for service discovery. This system also provides a number of core services that implement the diagram essentials.

Additionally, diagram-js defines a data model for graphical elements and their relationships.
Module System

Under the hood, diagram-js employs dependency injection (DI) to wire and discover diagram components. This mechanism is built on top of didi.

When talking about modules in the context of diagram-js, we refer to units that provide named services along with their implementation. A service in that sense is a function or instance that may consume other services to do stuff in the context of the diagram.

The following shows a service that hooks into life-cycle events. It does so by registering an event via the eventBus, another well-known service:

const MyLoggingPlugin = (eventBus) => {
  eventBus.on('element.changed', (event) => {
    console.log('element ', event.element, ' changed');
  });
}

// ensure the dependency names are still available after minification
MyLoggingPlugin.$inject = [ 'eventBus' ];

We must publish the service under a unique name using a module definition:

import CoreModule from 'diagram-js/lib/core';

// export as module
export default {
  __depends__: [ CoreModule ], // {2}
  __init__: [ 'myLoggingPlugin' ], // {3}
  myLoggingPlugin: [ 'type', MyLoggingPlugin ] // {1}
};

The definition tells the DI infrastructure that the service is called myLoggingPlugin {1}, that it depends on the diagram-js core module {2} and that the service should be initialized upon diagram creation {3}. For more details have a look at the didi documentation.

We may now bootstrap diagram-js, passing our custom module:

import MyLoggingModule from 'path-to-my-logging-module';

const diagram = new Diagram({
  modules: [
    MyLoggingModule
  ]
});

To plug in the module into bpmn-js, you would use the additionalModules option as shown in the Extend the Modeler section.
Core Services

The diagram-js core is built around a number of essential services:

    Canvas - provides APIs for adding and removing graphical elements; deals with element life cycle and provides APIs to zoom and scroll.

    EventBus - the library's global communication channel with a fire and forget policy. Interested parties can subscribe to various events and act upon them once they are emitted. The event bus helps us to decouple concerns and to modularize functionality so that new features can hook up easily with existing behavior.

    ElementFactory - a factory for creating shapes and connections according to diagram-js' internal data model.

    ElementRegistry - knows all elements added to the diagram and provides APIs to retrieve the elements and their graphical representation by id.

    GraphicsFactory - responsible for creating graphical representations of shapes and connections. The actual look and feel is defined by renderers, i.e. the DefaultRenderer inside the draw module.

Data Model

Under the hood, diagram-js implements a simple data model consisting of shapes and connections.
diagram-js data model: shapes and connections
Data Model Essentials: Shapes and Connections

A shape has a parent, a list of children as well as a list of incoming and outgoing connections.

A connection has a parent as well as a source and target, pointing to a shape.

The ElementRegistry is responsible for creating shapes and connections according to that model. During modeling, element relationships will be updated according to user operations by the Modeling service.
Auxiliary Services (i.e. the Toolbox)

Aside from the data model and its core services, diagram-js provides a rich toolbox of additional helpers.

    CommandStack - responsible for redo and undo during modeling.
    ContextPad - provides contextual actions around an element.
    Overlays - provides APIs for attaching additional information to diagram elements.
    Modeling - provides APIs for updating elements on the canvas (moving, deleting)
    Palette
    ...

Let's move on to the BPMN magic that is happening behind the scenes.
BPMN Meta-Model (bpmn-moddle)

bpmn-moddle encapsulates the BPMN 2.0 meta-model and provides us with facilities to read and write BPMN 2.0 XML documents. On import, it parses the XML document into a JavaScript object tree. That tree is edited and validated during modeling and then exported back to BPMN 2.0 XML once the user wishes to save the diagram. Because bpmn-moddle encapsulates knowledge about BPMN, we are able to validate during import and modeling. Based on the results, we can constrain certain modeling actions and output helpful error messages and warnings to the user.

Much like bpmn-js, the foundations of bpmn-moddle are built on top of two libraries:

    moddle which offers a concise way to define meta-models in JavaScript
    moddle-xml which reads and writes XML documents based on moddle

In essence bpmn-moddle adds the BPMN spec as a meta-model and offers a simple interface for BPMN schema validation. From the library perspective it provides the following API:

    fromXML - create a BPMN tree from a given XML string
    toXML - write a BPMN object tree to BPMN 2.0 XML

The BPMN meta-model is essential for bpmn-js, as it allows us to validate BPMN 2.0 documents we consume, provide proper modeling rules and export valid BPMN documents that all compliant BPMN modelers can understand.
Plugging Things Together (bpmn-js)

We learned bpmn-js is built on top of diagram-js and bpmn-moddle. It ties both together and adds the BPMN look and feel. This includes a BPMN palette, BPMN context pad as well as BPMN 2.0 specific rules. In this section, we'll be explaining how that works in different phases of modeling.

When we import a BPMN 2.0 document, it is parsed from XML into an object tree by bpmn-moddle. bpmn-js renders all visible elements of that tree, i.e. it creates the respective shapes and connections on the canvas. Thereby it ties both the BPMN elements and the graphical elements together. This results in a structure, as shown below, for a start event shape.

{
  id: 'StartEvent_1',
  x: 100,
  y: 100,
  width: 50,
  height: 50,
  businessObject: {
    $attrs: Object
    $parent: {
      $attrs: Object
      $parent: ModdleElement
      $type: 'bpmn:Process'
      flowElements: Array[1]
      id: 'Process_1'
      isExecutable: false
    }
    $type: 'bpmn:StartEvent'
    id: 'StartEvent_1'
  }
}

You may access the underlying BPMN type from each graphical element via the businessObject property.

bpmn-js also knows how each BPMN element looks like thanks to the BpmnRenderer. By plugging into the render cycle, you may also define custom representations of individual BPMN elements.

We can start modeling once the importing is done. We use rules to allow or disallow certain modeling operations. These rules are defined by BpmnRules. We base these rules on the BPMN 2.0 standard as defined by the OMG. However as mentioned earlier, others may also hook up with the rule evaluation to contribute different behavior.

The modeling module bundles BPMN 2.0 related modeling functionality. It adds BPMN 2.0 specific modeling behaviors and is responsible for updating the BPMN 2.0 document tree with every modeling operation carried out by the user (cf. BpmnUpdater). Check it out to get a deeper insight into rules, behaviors and the BPMN update cycle.

When looking at bpmn-js purely from the library perspective, it's worth mentioning it can be used in three variants:

    Viewer to display diagrams
    NavigatedViewer to display and navigate BPMN diagrams
    Modeler to model BPMN diagrams

The only difference between the versions is that they bundle a different set of functionality. The NavigatedViewer adds modules for navigating the canvas and the Modeler adds a whole lot of functionality for creating, editing and interacting with elements on the canvas.
Going Further

In the first part of this walkthrough, we focused on using bpmn-js as a BPMN viewer as well as a modeler. This should have given you a good understanding of the toolkit from the library perspective.

In the second part, we focused on bpmn-js internals. We presented diagram-js as well as bpmn-moddle, the two foundations bpmn-js is built upon and gave you an overview of how bpmn-js plugs all of these together.

There exists a number of additional resources that allow you to progress further:

    Examples - numerous examples that showcase how to embed and extend bpmn-js.
    Source Code (bpmn-js, diagram-js) - mostly well documented; should give you great insights into the library's internals.
    Forum - a good place to get help for using and extending bpmn-js.

Was there anything that we could have explained better / you got stuck with? Propose an improvement to this document or tell us about it in our forums.

Add BPMN diagrams to your application

Embed BPMN diagrams in your application with a few lines of code.

<script>
  const viewer = new BpmnJS({ container: 'body' });

  try {
    await viewer.importXML(bpmnXML);
  } catch (err) {
    console.error('error loading BPMN 2.0 XML', err);
  }
</script>