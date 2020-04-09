ro-crate-py
===========

Create/parse rocrate_ (Research Object Crate) metadata.

Note: **Under development**

License
-------

© 2019 Stian Soiland-Reyes <http://orcid.org/0000-0001-9842-9718>, The University of Manchester, UK

Licensed under the 
Apache License, version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>, 
see the file LICENSE.txt for details.

Contribute
----------

Source code: <https://github.com/researchobject/ro-crate-py>

Feel free to raise a pull request at <https://github.com/researchobject/ro-crate-py/pulls>
or an issue at <https://github.com/researchobject/ro-crate-py/issues>.

Submitted contributions are assumed to be covered by section 5 of the Apache License 2.0.

Installing
----------

You will need Python 3.4 or later (Recommended: 3.7).

If you want to install manually from this code base, then try::

    pip install .

..or if you use don't use `pip`::
    
    python setup.py install


.. _rocrate: https://w3id.org/ro/crate
.. _pip: https://docs.python.org/3/installing/


Example
-------

Creating a workflow RO-Crate

.. code-block:: python
    from rocrate import rocrate_api
    wf_path = "https://github.com/galaxyproject/SARS-CoV-2/blob/master/genomics/deploy/workflows/4-Variation.ga"
    files_list = ["https://github.com/galaxyproject/SARS-CoV-2/blob/master/genomics/4-Variation/SRR10903401.vcf.gz", "https://github.com/galaxyproject/SARS-CoV-2/blob/master/genomics/4-Variation/SRR11241255.vcf.gz"] 
    # Create base package
    wf_crate = rocrate_api.make_workflow_crate(wf_path,type="Galaxy",files_list)
    # Add authors info
    # ....
    # Write to zip file
    zip_out_path = "/home/test_user/wf_crate.zip"
    wf_crate.write_zip(zip_out_path)


