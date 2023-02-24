import datetime

# from tokenize import String
from io import StringIO
import urllib
import uuid
from io import BytesIO
from hashlib import md5
from pathlib import PurePosixPath
from typing import (
    Any,
    Dict,
    List,
    MutableSequence,
    Optional,
    Tuple,
    Union,
    cast,
)
from xmlrpc.client import Boolean

from prov.identifier import Identifier
from prov.model import PROV, PROV_LABEL, PROV_TYPE, PROV_VALUE, ProvDocument, ProvEntity

# import graphviz
from prov.dot import prov_to_dot
from tools.load_ga_export import load_ga_history_export, GalaxyJob, GalaxyDataset
from ast import literal_eval
import os

# from .errors import WorkflowException
# from .job import CommandLineJob, JobBase
# from .loghandler import #_logger
# from .process import Process, shortname
from rocrate.provenance_constants import (
    ACCOUNT_UUID,
    CWLPROV,
    METADATA,
    ORE,
    PROVENANCE,
    ENCODING,
    # TEXT_PLAIN,
    RO,
    SCHEMA,
    # SHA1,
    UUID,
    WF4EVER,
    WFDESC,
    WFPROV,
)

# from .stdfsaccess import StdFsAccess
# from rocrate.utils_cwl import CWLObjectType, JobsType, get_listing, posix_path, versionstring
# from .workflow_job import WorkflowJob

# if TYPE_CHECKING:
#     from rocrate.provenance import ResearchObject

from pathlib import Path


def posix_path(local_path: str) -> str:
    return str(PurePosixPath(Path(local_path)))


def remove_escapes(s):
    escapes = "".join([chr(char) for char in range(1, 32)])
    translator = str.maketrans("", "", escapes)
    s.translate(translator)


def reassign(d):
    for k, v in d.items():
        try:
            evald = literal_eval(v)
            if isinstance(evald, dict):
                d[k] = evald
        except ValueError:
            pass


class ProvenanceProfile:
    """\
    Provenance profile.

    Populated from a galaxy workflow export.
    """

    def __init__(
        self,
        ga_export_dir: Path,
        full_name: str = None,
        orcid: str = None,
        run_uuid: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Initialize the provenance profile.
        Keyword arguments:
            ga_export -- the galaxy metadata export (Dict)
            outpath --
            full_name -- author name (optional)
            orcid -- orcid (optional)
            prov_name -- provenance file name
            run_uuid -- uuid for the workflow run
        """
        self.orcid = orcid
        self.ga_export_dir = ga_export_dir
        self.ro_uuid = uuid.uuid4()
        # TODO: should be connected to a ro_crate?
        self.base_uri = "arcp://uuid,%s/" % self.ro_uuid
        self.document = ProvDocument()
        # TODO extract engine_uuid from galaxy, type: str
        self.engine_uuid = "urn:uuid:%s" % uuid.uuid4()  # type: str
        self.full_name = full_name
        # import galaxy history metadata
        metadata_export = load_ga_history_export(ga_export_dir)

        self.declared_strings_s = {}

        self.datasets = []
        for i, dataset in enumerate(metadata_export["datasets_attrs"]):
            datasets_attrs = GalaxyDataset()
            datasets_attrs.parse_ga_dataset_attrs(dataset)
            self.datasets.append(datasets_attrs.attributes)

        self.workflow_invocation_uuid = set()
        self.jobs = {}
        for i, job in enumerate(metadata_export["jobs_attrs"]):
            job_attrs = GalaxyJob()
            job_attrs.parse_ga_jobs_attrs(job)
            self.jobs[job_attrs.attributes["encoded_id"]] = job_attrs.attributes
            try:
                self.workflow_invocation_uuid.add(
                    job_attrs.attributes["parameters"]["__workflow_invocation_uuid__"]
                )
            except KeyError:
                pass

        if self.workflow_invocation_uuid:
            self.workflow_run_uuid = uuid.UUID(
                next(iter(self.workflow_invocation_uuid))
            )
            self.workflow_run_uri = self.workflow_run_uuid.urn  # type: str
        else:
            self.workflow_run_uuid = run_uuid or uuid.uuid4()
            self.workflow_run_uri = self.workflow_run_uuid.urn  # type: str

        self.generate_prov_doc()
        for v in self.jobs.values():
            self.declare_process(v)

    def __str__(self) -> str:
        """Represent this Provenvance profile as a string."""
        return "ProvenanceProfile <{}>".format(
            self.workflow_run_uri,
            # self.research_object, #?
        )

    def generate_prov_doc(self) -> Tuple[str, ProvDocument]:
        """Add basic namespaces."""
        # TODO:
        # can we identify a host where the workflow was executed?
        # should OnlineAccount be used to describe a galaxy user?
        # PROV_TYPE: FOAF["OnlineAccount"],
        # TODO: change how we register galaxy version, probably a declare_version func
        # self.galaxy_version = self.ga_export["jobs_attrs"][0]["galaxy_version"]
        # TODO: change notation to already imported namespaces?
        self.document.add_namespace("wfprov", "http://purl.org/wf4ever/wfprov#")
        # document.add_namespace('prov', 'http://www.w3.org/ns/prov#')
        self.document.add_namespace("wfdesc", "http://purl.org/wf4ever/wfdesc#")
        # TODO: Make this ontology. For now only has cwlprov:image
        self.document.add_namespace("cwlprov", "https://w3id.org/cwl/prov#")
        self.document.add_namespace("foaf", "http://xmlns.com/foaf/0.1/")
        self.document.add_namespace("schema", "http://schema.org/")
        self.document.add_namespace("orcid", "https://orcid.org/")
        self.document.add_namespace("id", "urn:uuid:")
        # NOTE: Internet draft expired 2004-03-04 (!)
        #  https://tools.ietf.org/html/draft-thiemann-hash-urn-01
        # TODO: Change to nih:sha-256; hashes
        #  https://tools.ietf.org/html/rfc6920#section-7
        self.document.add_namespace("data", "urn:hash::sha1:")

        self.provenance_ns = self.document.add_namespace(
            "provenance", self.base_uri + posix_path(PROVENANCE) + "/"
        )
        # TODO: use appropriate refs for ga_export and related inputs
        ro_identifier_workflow = self.base_uri + "ga_export" + "/"
        self.wf_ns = self.document.add_namespace("wf", ro_identifier_workflow)
        ro_identifier_input = self.base_uri + "ga_export/datasets#"
        self.document.add_namespace("input", ro_identifier_input)

        # More info about the account (e.g. username, fullname)
        # TODO: extract this info from galaxy somehow, probably only a username
        account = self.document.agent(ACCOUNT_UUID)
        if self.orcid or self.full_name:
            person = {PROV_TYPE: PROV["Person"], "prov:type": SCHEMA["Person"]}
            if self.full_name:
                person["prov:label"] = self.full_name
                person["foaf:name"] = self.full_name
                person["schema:name"] = self.full_name
            else:
                # TODO: Look up name from ORCID API?
                pass

            agent = self.document.agent(self.orcid or uuid.uuid4().urn, person)
            self.document.actedOnBehalfOf(account, agent)

        # The engine that executed the workflow
        wfengine = self.document.agent(
            self.engine_uuid,
            {
                PROV_TYPE: PROV["SoftwareAgent"],
                "prov:type": WFPROV["WorkflowEngine"],
                # TODO: get galaxy version
                "prov:label": "galaxy_version_placeholder",
            },
        )
        self.document.wasStartedBy(wfengine, None, account, datetime.datetime.now())
        # define workflow run level activity
        self.document.activity(
            self.workflow_run_uri,
            datetime.datetime.now(),
            None,
            {
                PROV_TYPE: WFPROV["WorkflowRun"],
                "prov:label": "Run of galaxy workflow",
            },
        )
        # association between SoftwareAgent and WorkflowRun
        main_workflow = "wf:main"
        self.document.wasAssociatedWith(
            self.workflow_run_uri, self.engine_uuid, main_workflow
        )
        self.document.wasStartedBy(
            self.workflow_run_uri, None, self.engine_uuid, datetime.datetime.now()
        )
        return (self.workflow_run_uri, self.document)

    def declare_process(
        self,
        # process_name: str,
        ga_export_jobs_attrs: dict,
        # when: datetime.datetime,
        process_run_id: Optional[str] = None,
    ) -> str:
        """Record the start of each Process."""
        if process_run_id is None:
            process_run_id = uuid.uuid4().urn

        process_name = ga_export_jobs_attrs["tool_id"]
        # tool_version = ga_export_jobs_attrs["tool_version"]
        # TODO: insert workflow id
        prov_label = "Run of " + process_name
        start_time = ga_export_jobs_attrs["create_time"]
        end_time = ga_export_jobs_attrs["update_time"]

        # TODO: Find out how to include commandline as a string
        # cmd = ga_export_jobs_attrs["command_line"]
        # cmd = self.document.entity(
        #     uuid.uuid4().urn,
        #     {PROV_TYPE: WFPROV["Artifact"], PROV_LABEL: ga_export_jobs_attrs["command_line"]}
        #     )

        self.document.activity(
            process_run_id,
            start_time,
            end_time,
            {
                PROV_TYPE: WFPROV["ProcessRun"],
                PROV_LABEL: prov_label,
                # PROV_LABEL: cmd
            },
        )
        self.document.wasAssociatedWith(
            process_run_id, self.engine_uuid, str("wf:main/" + process_name)
        )
        self.document.wasStartedBy(
            process_run_id, None, self.workflow_run_uri, start_time, None, None
        )
        self.used_artefacts(process_run_id, ga_export_jobs_attrs)
        return process_run_id

    def used_artefacts(
        self,
        process_run_id: str,
        process_metadata: dict,
        process_name: Optional[str] = None,
    ) -> None:
        """Add used() for each data artefact."""
        # FIXME: Use workflow name if available,
        # "main" is wrong for nested workflows
        base = "main"
        if process_name is not None:
            base += "/" + process_name
        tool_id = process_metadata["tool_id"]
        base += "/" + tool_id
        items = ["inputs", "outputs", "parameters"]
        for item in items:
            for key, value in process_metadata[item].items():
                if not value:
                    pass
                # if "json" in key:
                #     value = json.loads(value)
                if isinstance(key, str):
                    key = key.replace("|", "_")
                if isinstance(value, str):
                    value = value.replace("|", "_")

                prov_role = self.wf_ns[f"{base}/{key}"]

                # if not value or len(value) == 0:
                if item in ("inputs", "outputs"):
                    for v in value:
                        for d in self.datasets:
                            if v in (
                                [d["encoded_id"]]
                                + d["copied_from_history_dataset_association_id_chain"]
                            ):
                                self.declare_entity(process_run_id, d, prov_role)
                # else:
                #     self.declare_entity(process_run_id, value, prov_role)

    def declare_entity(self, process_run_id, value, prov_role) -> None:
        try:
            entity = self.declare_artefact(value)
            self.document.used(
                process_run_id,
                entity,
                datetime.datetime.now(),
                None,
                {"prov:role": prov_role},
            )
        except OSError:
            pass

    def declare_artefact(self, value: Any) -> ProvEntity:
        """Create data artefact entities for all file objects."""
        if value is None:
            # FIXME: If this can happen we'll need a better way to
            # represent this in PROV
            return self.document.entity(CWLPROV["None"], {PROV_LABEL: "None"})

        if isinstance(value, (bool, int, float)):
            # Typically used in job documents for flags

            # FIXME: Make consistent hash URIs for these
            # that somehow include the type
            # (so "1" != 1 != "1.0" != true)
            entity = self.document.entity(uuid.uuid4().urn, {PROV_VALUE: value})
            # self.research_object.add_uri(entity.identifier.uri)
            return entity

        if isinstance(value, str):
            # clean up unwanted characters
            # value = value.replace("|", "_")
            (entity, _) = self.declare_string(value)
            return entity

        if isinstance(value, bytes):
            # If we got here then we must be in Python 3
            # byte_s = BytesIO(value)
            # data_file = self.research_object.add_data_file(byte_s)
            # FIXME: Don't naively assume add_data_file uses hash in filename!
            data_id = "data:%s" % str(value)  # PurePosixPath(data_file).stem
            return self.document.entity(
                data_id,
                {PROV_TYPE: WFPROV["Artifact"], PROV_VALUE: str(value)},
            )

        if isinstance(value, Dict):
            if "@id" in value:
                # Already processed this value,
                # but it might not be in this PROV
                entities = self.document.get_record(value["@id"])
                if entities:
                    return entities[0]
                # else, unknown in PROV, re-add below as if it's fresh

            # Base case - we found a File we need to update
            if value.get("class") == "File":
                entity = self.declare_file(value)
                value["@id"] = entity.identifier.uri
                return entity

            if value.get("class") == "Directory":
                entity = self.declare_directory(value)
                value["@id"] = entity.identifier.uri
                return entity
            coll_id = value.setdefault("@id", uuid.uuid4().urn)
            # some other kind of dictionary?
            # TODO: also Save as JSON
            coll = self.document.entity(
                coll_id,
                [
                    (PROV_TYPE, WFPROV["Artifact"]),
                    (PROV_TYPE, PROV["Collection"]),
                    (PROV_TYPE, PROV["Dictionary"]),
                ],
            )

            if value.get("class"):
                # _logger.warning("Unknown data class %s.", value["class"])
                # FIXME: The class might be "http://example.com/somethingelse"
                coll.add_asserted_type(CWLPROV[value["class"]])q

    def declare_file(self, value: Dict) -> Tuple[ProvEntity, ProvEntity, str]:
        if value["class"] != "File":
            raise ValueError("Must have class:File: %s" % value)

        # Track filename and extension, this is generally useful only for
        # secondaryFiles. Note that multiple uses of a file might thus record
        # different names for the same entity, so we'll
        # make/track a specialized entity by UUID
        file_id = value.setdefault("@id", uuid.UUID(value["dataset_uuid"]).urn)
        # A specialized entity that has just these names
        file_entity = self.document.entity(
            file_id,
            [(PROV_TYPE, WFPROV["Artifact"]), (PROV_TYPE, WF4EVER["File"])],
        )  # type: ProvEntity

        if "name" in value:
            file_entity.add_attributes({CWLPROV["basename"]: value["name"]})
        # if "nameroot" in value:
        #     file_entity.add_attributes({CWLPROV["nameroot"]: value["nameroot"]})
        if "extension" in value:
            file_entity.add_attributes({CWLPROV["nameext"]: value["extension"]})
        # self.document.specializationOf(file_entity, entity)

        return file_entity  # , entity, checksum

    def declare_string(self, value: str) -> Tuple[ProvEntity, str]:
        """Save as string in UTF-8."""
        value = str(value).replace("|", "_")
        byte_s = BytesIO(str(value).encode(ENCODING))
        # data_file = self.research_object.add_data_file(byte_s, content_type=TEXT_PLAIN)
        checksum = md5(byte_s.getbuffer()).hexdigest()
        self.declared_strings_s[checksum] = byte_s

        # FIXME: Don't naively assume add_data_file uses hash in filename!
        data_id = "data:%s" % checksum  # PurePosixPath(data_file).stem
        entity = self.document.entity(
            data_id, {PROV_TYPE: WFPROV["Artifact"], PROV_VALUE: str(value)}
        )  # type: ProvEntity
        return entity, checksum  # , data_file

    def generate_output_prov(
        self,
        final_output: Union[Dict, None],
        process_run_id: Optional[str],
        name: Optional[str],
    ) -> None:
        """Call wasGeneratedBy() for each output,copy the files into the RO."""
        if isinstance(final_output, MutableSequence):
            for entry in final_output:
                self.generate_output_prov(entry, process_run_id, name)
        elif final_output is not None:
            # Timestamp should be created at the earliest
            timestamp = datetime.datetime.now()

            # For each output, find/register the corresponding
            # entity (UUID) and document it as generated in
            # a role corresponding to the output
            for output, value in final_output.items():
                entity = self.declare_artefact(value)
                if name is not None:
                    name = urllib.parse.quote(str(name), safe=":/,#")
                    # FIXME: Probably not "main" in nested workflows
                    role = self.wf_ns[f"main/{name}/{output}"]
                else:
                    role = self.wf_ns["main/%s" % output]

                if not process_run_id:
                    process_run_id = self.workflow_run_uri

                self.document.wasGeneratedBy(
                    entity, process_run_id, timestamp, None, {"prov:role": role}
                )

    def finalize_prov_profile(
        self, out_path: Path = None, serialize: Boolean = False, name=None
    ):
        # type: (Optional[str],Optional[bool],Optional[str]) -> Tuple[Dict,List[Identifier]]
        """Transfer the provenance related files to the RO-crate"""
        # NOTE: Relative posix path
        if name is None:
            # main workflow, fixed filenames
            filename = "ga_export.cwlprov"
        else:
            # ASCII-friendly filename,
            # avoiding % as we don't want %2520 in manifest.json
            wf_name = urllib.parse.quote(str(name), safe="").replace("%", "_")
            # Note that the above could cause overlaps for similarly named
            # workflows, but that's OK as we'll also include run uuid
            # which also covers thhe case of this step being run in
            # multiple places or iterations
            filename = f"{wf_name}.{self.workflow_run_uuid}.cwlprov"

        # print(basename)
        # serialized prov documents
        serialized_prov_docs = {}
        # list of prov identifiers of provenance files
        prov_ids = []
        # https://www.w3.org/TR/prov-xml/
        serialized_prov_docs[filename + ".xml"] = StringIO(
            self.document.serialize(format="xml", indent=4)
        )
        prov_ids.append(self.provenance_ns[filename + ".xml"])
        # https://www.w3.org/TR/prov-n/
        serialized_prov_docs[filename + ".provn"] = StringIO(
            self.document.serialize(format="provn", indent=2)
        )
        prov_ids.append(self.provenance_ns[filename + ".provn"])
        # https://www.w3.org/Submission/prov-json/
        serialized_prov_docs[filename + ".json"] = StringIO(
            self.document.serialize(format="json", indent=2)
        )
        prov_ids.append(self.provenance_ns[filename + ".json"])

        # "rdf" aka https://www.w3.org/TR/prov-o/
        # which can be serialized to ttl/nt/jsonld (and more!)

        # https://www.w3.org/TR/turtle/
        serialized_prov_docs[filename + ".ttl"] = StringIO(
            self.document.serialize(format="rdf", rdf_format="turtle")
        )
        prov_ids.append(self.provenance_ns[filename + ".ttl"])
        # https://www.w3.org/TR/n-triples/
        serialized_prov_docs[filename + ".nt"] = StringIO(
            self.document.serialize(format="rdf", rdf_format="ntriples")
        )
        prov_ids.append(self.provenance_ns[filename + ".nt"])
        # https://www.w3.org/TR/json-ld/
        # TODO: Use a nice JSON-LD context
        # see also https://eprints.soton.ac.uk/395985/
        # 404 Not Found on https://provenance.ecs.soton.ac.uk/prov.jsonld :
        serialized_prov_docs[filename + ".jsonld"] = StringIO(
            self.document.serialize(format="rdf", rdf_format="json-ld")
        )
        prov_ids.append(self.provenance_ns[filename + ".jsonld"])

        graph = prov_to_dot(self.document).to_string()
        # graph_s = graph_dot
        # print(type(graph))
        graph_s = StringIO()
        graph_s.write(graph)
        # dot.write_png(basename + '.png')

        if serialize:
            if out_path is not None:
                basename = str(PurePosixPath(out_path) / filename)
            else:
                basename = filename

            if not os.path.exists(out_path):
                os.makedirs(out_path)

            with open(basename + ".xml", "w") as provenance_file:
                self.document.serialize(provenance_file, format="xml", indent=4)

            with open(basename + ".provn", "w") as provenance_file:
                self.document.serialize(provenance_file, format="provn", indent=2)

            with open(basename + ".json", "w") as provenance_file:
                self.document.serialize(provenance_file, format="json", indent=2)

            with open(basename + ".ttl", "w") as provenance_file:
                self.document.serialize(
                    provenance_file, format="rdf", rdf_format="turtle"
                )

            with open(basename + ".nt", "w") as provenance_file:
                self.document.serialize(
                    provenance_file, format="rdf", rdf_format="ntriples"
                )

            with open(basename + ".jsonld", "w") as provenance_file:
                self.document.serialize(
                    provenance_file, format="rdf", rdf_format="json-ld"
                )

            # _logger.debug("[provenance] added provenance: %s", prov_ids)
        return (serialized_prov_docs, prov_ids, graph_s)
