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
        # prov_name: str = None,
        # prov_path: Path = None,
        # fsaccess: StdFsAccess,
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
        # self.fsaccess = fsaccess
        self.orcid = orcid
        self.ga_export_dir = ga_export_dir
        # TODO: does it make sense to write all outputs to a tmp dir
        # chance that temp dir doesnt get removed properly
        # if out_path is None:
        #     self.out_path = tempfile.mkdtemp()
        self.ro_uuid = uuid.uuid4()
        # TODO: should be connected to a ro_crate?
        self.base_uri = "arcp://uuid,%s/" % self.ro_uuid
        self.document = ProvDocument()
        # TODO extract engine_uuid from galaxy, type: str
        self.engine_uuid = "urn:uuid:%s" % uuid.uuid4()  # type: str
        self.full_name = full_name
        # TODO move to separate function
        metadata_export = load_ga_history_export(ga_export_dir)
        # self.tmp_dir = tempfile.mkdtemp()
        self.declared_strings_s = {}

        self.datasets = []
        # print(metadata_export["jobs_attrs"][0]["params"])
        for i, dataset in enumerate(metadata_export["datasets_attrs"]):
            datasets_attrs = GalaxyDataset()
            datasets_attrs.parse_ga_dataset_attrs(dataset)
            # print(i)
            # print(datasets_attrs.attributes['encoded_id'])
            self.datasets.append(datasets_attrs.attributes)
            # self.declare_process(ds_attrs.attributes)

        # print(self.datasets)

        # print([[d['encoded_id']]+d['copied_from_history_dataset_association_id_chain'] for d in self.datasets])
        self.workflow_invocation_uuid = set()
        self.jobs = {}
        for i, job in enumerate(metadata_export["jobs_attrs"]):
            job_attrs = GalaxyJob()
            job_attrs.parse_ga_jobs_attrs(job)
            # print(i)
            # print(job_attrs.attributes)
            # for k, v in job_attrs.attributes['parameters'].items():
            #     print(k, "      :     ", v)
            self.jobs[job_attrs.attributes["encoded_id"]] = job_attrs.attributes
            try:
                self.workflow_invocation_uuid.add(
                    job_attrs.attributes["parameters"]["__workflow_invocation_uuid__"]
                )
            except KeyError:
                pass
            # print('set:')
            # print(self.workflow_invocation_uuid)
            # print("inputs")
            # print(job_attrs.attributes["inputs"])
            # print("outputs")
            # print(job_attrs.attributes["outputs"])

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

        # print(os.listdir(tempfile.gettempdir()))

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
        # Also needed for docker images
        # self.document.add_namespace(SHA256, "nih:sha-256;")

        # Pre-register provenance directory so we can refer to its files
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
        # TODO: change to workflow invocation id?
        if process_run_id is None:
            process_run_id = uuid.uuid4().urn

        # cmd = ga_export_jobs_attrs["command_line"]
        process_name = ga_export_jobs_attrs["tool_id"]
        # tool_version = ga_export_jobs_attrs["tool_version"]
        # TODO: insert workflow id
        prov_label = "Run of " + process_name
        start_time = ga_export_jobs_attrs["create_time"]
        end_time = ga_export_jobs_attrs["update_time"]

        # TODO: Find out how to include commandline as a string
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
                # TODO: Find out how to include commandline as a string
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
        # self.generate_output_prov(outputs, process_run_id, process_name)
        # self.document.wasEndedBy(process_run_id, None, self.workflow_run_uri, when)
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
        # print(process_metadata["params"])
        for item in items:
            # print(item)
            # print("-----------")
            # print(process_metadata[item])
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
                # print("key  : ", key)
                # print("-----------")
                # print("value: ", value)
                # print("-----------")
                # print("type : ", type(value))
                # print("-----------")

                if item in ("inputs", "outputs"):
                    for v in value:
                        for d in self.datasets:
                            # print([d['encoded_id']])
                            # print(d['copied_from_history_dataset_association_id_chain'])
                            if v in (
                                [d["encoded_id"]]
                                + d["copied_from_history_dataset_association_id_chain"]
                            ):
                                self.declare_entity(process_run_id, d, prov_role)
                else:
                    self.declare_entity(process_run_id, value, prov_role)

    def declare_entity(self, process_run_id, value, prov_role) -> None:
        try:
            entity = self.declare_artefact(value)
            # print("test2")
            # print(entity)
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
            # print(value)

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
            # print("value: ", value)
            # print("-----------")
            # print("type : ", type(value))
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
                coll.add_asserted_type(CWLPROV[value["class"]])

            # Let's iterate and recurse
            coll_attribs = []  # type: List[Tuple[Identifier, ProvEntity]]
            for (key, val) in value.items():
                # clean up unwanted characters
                if isinstance(key, str):
                    key = key.replace("|", "_")
                if isinstance(val, str):
                    val = val.replace("|", "_")

                v_ent = self.declare_artefact(val)
                self.document.membership(coll, v_ent)
                m_entity = self.document.entity(uuid.uuid4().urn)
                # Note: only support PROV-O style dictionary
                # https://www.w3.org/TR/prov-dictionary/#dictionary-ontological-definition
                # as prov.py do not easily allow PROV-N extensions
                m_entity.add_asserted_type(PROV["KeyEntityPair"])
                m_entity.add_attributes(
                    {PROV["pairKey"]: str(key), PROV["pairEntity"]: v_ent}
                )
                coll_attribs.append((PROV["hadDictionaryMember"], m_entity))
            coll.add_attributes(coll_attribs)
            # self.research_object.add_uri(coll.identifier.uri)
            return coll

        # some other kind of Collection?
        # TODO: also save as JSON
        try:
            members = []
            for each_input_obj in iter(value):
                # Recurse and register any nested objects
                e = self.declare_artefact(each_input_obj)
                members.append(e)

            # If we reached this, then we were allowed to iterate
            coll = self.document.entity(
                uuid.uuid4().urn,
                [
                    (PROV_TYPE, WFPROV["Artifact"]),
                    (PROV_TYPE, PROV["Collection"]),
                ],
            )
            if not members:
                coll.add_asserted_type(PROV["EmptyCollection"])
            else:
                for member in members:
                    # FIXME: This won't preserve order, for that
                    # we would need to use PROV.Dictionary
                    # with numeric keys
                    self.document.membership(coll, member)
            # self.research_object.add_uri(coll.identifier.uri)
            # FIXME: list value does not support adding "@id"
            return coll
        except TypeError:
            # _logger.warning("Unrecognized type %s of %r", type(value), value)
            # Let's just fall back to Python repr()
            entity = self.document.entity(uuid.uuid4().urn, {PROV_LABEL: repr(value)})
            # self.research_object.add_uri(entity.identifier.uri)
            return entity

    def declare_file(self, value: Dict) -> Tuple[ProvEntity, ProvEntity, str]:
        if value["class"] != "File":
            raise ValueError("Must have class:File: %s" % value)
        # Need to determine file hash aka RO filename
        # TODO: do we need a checksum value?
        # entity = None  # type: Optional[ProvEntity]
        # checksum = None
        # if "checksum" in value:
        #     csum = cast(str, value["checksum"])
        #     (method, checksum) = csum.split("$", 1)
        #     if method == SHA1:  # and self.research_object.has_data_file(checksum):
        #         entity = self.document.entity("data:" + checksum)

        # if not entity and "location" in value:
        #     location = str(value["location"])
        #     # If we made it here, we'll have to add it to the RO
        #     with self.fsaccess.open(location, "rb") as fhandle:
        #         relative_path = self.research_object.add_data_file(fhandle)
        #         # FIXME: This naively relies on add_data_file setting hash as filename
        #         checksum = PurePath(relative_path).name
        #         entity = self.document.entity(
        #             "data:" + checksum, {PROV_TYPE: WFPROV["Artifact"]}
        #         )
        #         if "checksum" not in value:
        #             value["checksum"] = f"{SHA1}${checksum}"

        # if not entity and "contents" in value:
        #     # Anonymous file, add content as string
        #     entity, checksum = self.declare_string(cast(str, value["contents"]))

        # # By here one of them should have worked!
        # if not entity or not checksum:
        #     raise ValueError(
        #         "class:File but missing checksum/location/content: %r" % value
        #     )

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

        # TODO: figure out if we need to keep track of derived files
        # Check for secondaries
        # for sec in cast(
        #     # MutableSequence[CWLObjectType],
        #     value.get("secondaryFiles", [])  # noqa
        # ):
        #     # TODO: Record these in a specializationOf entity with UUID?
        #     if sec["class"] == "File":
        #         (sec_entity, _, _) = self.declare_file(sec)
        #     elif sec["class"] == "Directory":
        #         sec_entity = self.declare_directory(sec)
        #     else:
        #         raise ValueError(f"Got unexpected secondaryFiles value: {sec}")
        #     # We don't know how/when/where the secondary file was generated,
        #     # but CWL convention is a kind of summary/index derived
        #     # from the original file. As its generally in a different format
        #     # then prov:Quotation is not appropriate.
        #     self.document.derivation(
        #         sec_entity,
        #         file_entity,
        #         other_attributes={PROV["type"]: CWLPROV["SecondaryFile"]},
        #     )

        return file_entity  # , entity, checksum

    def declare_directory(
        self,
        # value: CWLObjectType
        value,
    ) -> ProvEntity:
        """Register any nested files/directories."""
        # FIXME: Calculate a hash-like identifier for directory
        # so we get same value if it's the same filenames/hashes
        # in a different location.
        # For now, mint a new UUID to identify this directory, but
        # attempt to keep it inside the value dictionary
        dir_id = cast(str, value.setdefault("@id", uuid.uuid4().urn))

        # New annotation file to keep the ORE Folder listing
        ore_doc_fn = dir_id.replace("urn:uuid:", "directory-") + ".ttl"
        dir_bundle = self.document.bundle(self.metadata_ns[ore_doc_fn])

        coll = self.document.entity(
            dir_id,
            [
                (PROV_TYPE, WFPROV["Artifact"]),
                (PROV_TYPE, PROV["Collection"]),
                (PROV_TYPE, PROV["Dictionary"]),
                (PROV_TYPE, RO["Folder"]),
            ],
        )
        # ORE description of ro:Folder, saved separately
        coll_b = dir_bundle.entity(
            dir_id,
            [(PROV_TYPE, RO["Folder"]), (PROV_TYPE, ORE["Aggregation"])],
        )
        self.document.mentionOf(dir_id + "#ore", dir_id, dir_bundle.identifier)

        # dir_manifest = dir_bundle.entity(
        #     dir_bundle.identifier, {PROV["type"]: ORE["ResourceMap"],
        #                             ORE["describes"]: coll_b.identifier})

        coll_attribs = [(ORE["isDescribedBy"], dir_bundle.identifier)]
        coll_b_attribs = []  # type: List[Tuple[Identifier, ProvEntity]]

        # FIXME: .listing might not be populated yet - hopefully
        # a later call to this method will sort that
        is_empty = True

        # if "listing" not in value:
        #     get_listing(self.fsaccess, value)
        for entry in cast(Dict, value.get("listing", [])):
            is_empty = False
            # Declare child-artifacts
            entity = self.declare_artefact(entry)
            self.document.membership(coll, entity)
            # Membership relation aka our ORE Proxy
            m_id = uuid.uuid4().urn
            m_entity = self.document.entity(m_id)
            m_b = dir_bundle.entity(m_id)

            # PROV-O style Dictionary
            # https://www.w3.org/TR/prov-dictionary/#dictionary-ontological-definition
            # ..as prov.py do not currently allow PROV-N extensions
            # like hadDictionaryMember(..)
            m_entity.add_asserted_type(PROV["KeyEntityPair"])

            m_entity.add_attributes(
                {
                    PROV["pairKey"]: entry["basename"],
                    PROV["pairEntity"]: entity,
                }
            )

            # As well as a being a
            # http://wf4ever.github.io/ro/2016-01-28/ro/#FolderEntry
            m_b.add_asserted_type(RO["FolderEntry"])
            m_b.add_asserted_type(ORE["Proxy"])
            m_b.add_attributes(
                {
                    RO["entryName"]: entry["basename"],
                    ORE["proxyIn"]: coll,
                    ORE["proxyFor"]: entity,
                }
            )
            coll_attribs.append((PROV["hadDictionaryMember"], m_entity))
            coll_b_attribs.append((ORE["aggregates"], m_b))

        coll.add_attributes(coll_attribs)
        coll_b.add_attributes(coll_b_attribs)

        # Also Save ORE Folder as annotation metadata
        ore_doc = ProvDocument()
        ore_doc.add_namespace(ORE)
        ore_doc.add_namespace(RO)
        ore_doc.add_namespace(UUID)
        ore_doc.add_bundle(dir_bundle)
        ore_doc = ore_doc.flattened()
        ore_doc_path = str(PurePosixPath(METADATA, ore_doc_fn))
        with self.research_object.write_bag_file(ore_doc_path) as provenance_file:
            ore_doc.serialize(provenance_file, format="rdf", rdf_format="turtle")
        self.research_object.add_annotation(
            dir_id, [ore_doc_fn], ORE["isDescribedBy"].uri
        )

        if is_empty:
            # Empty directory
            coll.add_asserted_type(PROV["EmptyCollection"])
            coll.add_asserted_type(PROV["EmptyDictionary"])
        # self.research_object.add_uri(coll.identifier.uri)
        return coll

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

    def prospective_prov(self, job: GalaxyJob) -> None:
        """Create prospective prov recording as wfdesc prov:Plan."""
        if not isinstance(job, GalaxyJob):
            # direct command line tool execution
            self.document.entity(
                "wf:main",
                {
                    PROV_TYPE: WFDESC["Process"],
                    "prov:type": PROV["Plan"],
                    "prov:label": "Prospective provenance",
                },
            )
            return

        self.document.entity(
            "wf:main",
            {
                PROV_TYPE: WFDESC["Workflow"],
                "prov:type": PROV["Plan"],
                "prov:label": "Prospective provenance",
            },
        )

        for step in job.steps:
            stepnametemp = "wf:main/" + str(step.name)[5:]
            stepname = urllib.parse.quote(stepnametemp, safe=":/,#")
            provstep = self.document.entity(
                stepname,
                {PROV_TYPE: WFDESC["Process"], "prov:type": PROV["Plan"]},
            )
            self.document.entity(
                "wf:main",
                {
                    "wfdesc:hasSubProcess": provstep,
                    "prov:label": "Prospective provenance",
                },
            )
        # TODO: Declare roles/parameters as well

    def activity_has_provenance(self, activity, prov_ids):
        # type: (str, List[Identifier]) -> None
        """Add http://www.w3.org/TR/prov-aq/ relations to nested PROV files."""
        # NOTE: The below will only work if the corresponding metadata/provenance arcp URI
        # is a pre-registered namespace in the PROV Document
        attribs = [(PROV["has_provenance"], prov_id) for prov_id in prov_ids]
        self.document.activity(activity, other_attributes=attribs)
        # Tip: we can't use https://www.w3.org/TR/prov-links/#term-mention
        # as prov:mentionOf() is only for entities, not activities
        # uris = [i.uri for i in prov_ids]
        # self.research_object.add_annotation(activity, uris, PROV["has_provenance"].uri)

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
