.. _extensions:

Extensions for Sismic
=====================

Sismic can be quite easily extended to support other semantics, other code evaluators or even other features.
The `sismic-extensions <https://github.com/AlexandreDecan/sismic-extensions>`__ repository already provides
some extensions. Feel free to contact us if you developed an extension you would want to be listed here.


sismic-amola
------------

This extension provides support to import and export statechart written using AMOLA. This allows statecharts to be
created, edited and displayed with the `ASEME IDE <http://aseme.tuc.gr/>`__.
It exposes ``import_from_amola`` and ``export_to_amola`` based on the bundled Ecore meta-model (see *amola.ecore*).

Download: `https://github.com/AlexandreDecan/sismic-extensions/tree/master/sismic_amola <https://github.com/AlexandreDecan/sismic-extensions/tree/master/sismic_amola>`__


sismic-semantics
----------------

This extension contains two variations around the default interpreter: one supporting outer-first/source-state semantics,
and a second giving priority to transitions with event (instead of eventless transitions).

The extension provides two new interpreter classes: ``OuterFirstInterpreter`` and ``EventFirstInterpreter``.
These two interpreters can be combined together, thanks to Python multiple inheritance.

Download: `https://github.com/AlexandreDecan/sismic-extensions/tree/master/sismic_semantics <https://github.com/AlexandreDecan/sismic-extensions/tree/master/sismic_semantics>`__


