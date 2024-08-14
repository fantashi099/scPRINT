from lightning.pytorch.cli import LightningCLI, _get_short_description
from lightning.pytorch.callbacks import EarlyStopping
from lightning.pytorch.callbacks import LearningRateMonitor
from .trainer import TrainingMode
from lightning.pytorch.callbacks import ModelCheckpoint
from lightning.pytorch.callbacks import StochasticWeightAveraging
import torch
from jsonargparse import class_from_function

from scprint.tasks import Embedder, GNInfer, Denoiser

TASKS = [("embed", Embedder), ("gninfer", GNInfer), ("denoise", Denoiser)]


class MyCLI(LightningCLI):
    """
    MyCLI is a subclass of LightningCLI to add some missing params and create bindings between params of the model and the data.

    Used to allow calling denoise / embed / gninfer from the command line.
    Also to add more parameters and link parameters between the scdataloader and the scPRINT model.
    """

    def add_arguments_to_parser(self, parser):
        parser.add_lightning_class_args(EarlyStopping, "scprint_early_stopping")
        parser.set_defaults(
            {
                "scprint_early_stopping.monitor": "val_loss",
                "scprint_early_stopping.patience": 3,
            }
        )
        parser.add_lightning_class_args(
            LearningRateMonitor, "scprint_learning_rate_monitor"
        )
        parser.set_defaults({"scprint_learning_rate_monitor.logging_interval": "epoch"})
        parser.add_lightning_class_args(TrainingMode, "scprint_training")
        parser.link_arguments(
            "data.gene_pos", "model.gene_pos_enc", apply_on="instantiate"
        )
        parser.link_arguments("data.genes", "model.genes", apply_on="instantiate")
        parser.link_arguments(
            "data.decoders", "model.label_decoders", apply_on="instantiate"
        )
        parser.link_arguments(
            "data.labels_hierarchy", "model.labels_hierarchy", apply_on="instantiate"
        )
        parser.link_arguments("data.classes", "model.classes", apply_on="instantiate")
        parser.link_arguments(
            "data.gene_embeddings", "model.precpt_gene_emb", apply_on="parse"
        )
        parser.link_arguments("data.organisms", "model.organisms", apply_on="parse")
        parser.link_arguments(
            "data.num_datasets", "model.num_batch_labels", apply_on="instantiate"
        )
        parser.add_argument("--set_float32_matmul_precision", type=bool, default=False)
        parser.add_argument("--wandblog", type=str, default="")
        parser.add_argument("--log_freq", type=int, default=500)
        parser.add_argument("--log_graph", type=bool, default=False)
        parser.add_argument("--project", type=str)

    def _add_subcommands(self, parser, **kwargs) -> None:
        """Adds subcommands to the input parser."""
        self._subcommand_parsers = {}
        parser_subcommands = parser.add_subcommands()
        # the user might have passed a builder function
        trainer_class = (
            self.trainer_class
            if isinstance(self.trainer_class, type)
            else class_from_function(self.trainer_class)
        )
        # register all subcommands in separate subcommand parsers under the main parser
        for subcommand in self.subcommands():
            fn = getattr(trainer_class, subcommand)
            # extract the first line description in the docstring for the subcommand help message
            description = _get_short_description(fn)
            subparser_kwargs = kwargs.get(subcommand, {})
            subparser_kwargs.setdefault("description", description)
            subcommand_parser = self._prepare_subcommand_parser(
                trainer_class, subcommand, **subparser_kwargs
            )
            self._subcommand_parsers[subcommand] = subcommand_parser
            parser_subcommands.add_subcommand(
                subcommand, subcommand_parser, help=description
            )
        for subcommand in TASKS:
            fn = getattr(subcommand[1], "__init__")
            description = _get_short_description(fn)
            subparser_kwargs = {}
            subparser_kwargs.setdefault("description", description)
            parser = self.init_parser(**subparser_kwargs)
            parser.add_argument(
                "--ckpt_path",
                type=str,
                help=("Path to the checkpoint to load."),
                required=True,
            )
            parser.add_argument(
                "--output_filename",
                type=str,
                help=("Path to the output file(s)."),
                required=True,
            )
            parser.add_argument(
                "--adata", type=str, help=("Path to the anndata file."), required=True
            )
            if subcommand[0] == "gninfer":
                parser.add_argument(
                    "--cell_type",
                    type=str,
                    help=("The cell type to infer the gene regulatory network."),
                    required=True,
                )
            parser.add_argument("--seed_everything", type=int, default=42)
            parser.add_argument(
                "--species",
                type=str,
                help=(
                    "If not included in the anndata under 'organism_ontology_term_id', the species of the dataset."
                ),
                required=True,
            )
            parser.add_class_arguments(subcommand[1])
            added = parser.add_method_arguments(
                subcommand[1],
                "__call__",
                skip=set(["model", "adata", "cell_type"]),
            )
            self._subcommand_method_arguments[subcommand] = added
            self._subcommand_parsers[subcommand[0]] = parser
            parser_subcommands.add_subcommand(subcommand[0], parser, help=description)

    def _run_subcommand(self, subcommand: str) -> None:
        """Run the chosen subcommand."""
        before_fn = getattr(self, f"before_{subcommand}", None)
        if callable(before_fn):
            before_fn()
        if subcommand in self.subcommands():
            klass = self.trainer
            default = getattr(klass, subcommand)
            fn = getattr(self, subcommand, default)
            fn_kwargs = self._prepare_subcommand_kwargs(subcommand)
            fn(**fn_kwargs)
            after_fn = getattr(self, f"after_{subcommand}", None)
            if callable(after_fn):
                after_fn()
        else:
            import scanpy as sc
            from scprint import scPrint
            from scdataloader import Preprocessor
            import numpy as np

            adata = sc.read_h5ad(self.config_init[subcommand]["adata"])
            adata.obs.drop(columns="is_primary_data", inplace=True, errors="ignore")
            adata.obs["organism_ontology_term_id"] = self.config_init[subcommand][
                "species"
            ]
            preprocessor = Preprocessor(
                do_postp=False,
                force_preprocess=True,
            )
            adata = preprocessor(adata)
            conf = dict(self.config_init[subcommand])

            model = scPrint.load_from_checkpoint(
                self.config_init[subcommand]["ckpt_path"], precpt_gene_emb=None
            )
            for key in [
                "seed_everything",
                "config",
                "species",
                "cache",
                "ckpt_path",
                "adata",
                "output_filename",
                "cell_type",
            ]:
                conf.pop(key, None)

            if subcommand == "embed":
                emb = Embedder(**conf)
                print("embedding...")
                adata, metrics = emb(
                    model=model,
                    adata=adata,
                )
                # save the anndata
                print("metrics:")
                print(metrics)
                print()
                print(
                    "saving the file under the path: ",
                    self.config_init[subcommand]["output_filename"],
                )
                adata.write(
                    self.config_init[subcommand]["output_filename"] + "_embedded.h5ad"
                )

            if subcommand == "gninfer":
                gn = GNInfer(**conf)
                adata = gn(
                    model=model,
                    adata=adata,
                    cell_type=self.config_init[subcommand]["cell_type"],
                )
                print(
                    "saving the file under the path: ",
                    self.config_init[subcommand]["output_filename"],
                )
                adata.write(
                    self.config_init[subcommand]["output_filename"]
                    + "_"
                    + self.config_init[subcommand]["cell_type"]
                    + "_grn.h5ad"
                )

            if subcommand == "denoise":
                dn = Denoiser(**conf)
                metrics, random_indices, genes, expr_pred = dn(
                    model=model,
                    adata=adata,
                )
                print("metrics:")
                print(metrics)
                print()
                # now what we are doing here it to complete the expression profile with the denoised values. this is not done by default for now
                i = 0
                adata.X = adata.X.tolil()
                elems = (
                    random_indices
                    if random_indices is not None
                    else range(adata.shape[0])
                )
                for idx in elems[: dn.plot_corr_size]:
                    adata.X[
                        idx,
                        adata.var.index.get_indexer(
                            np.array(model.genes)[genes[i]]
                            if self.config_init[subcommand]["how"] != "most var"
                            else genes
                        ),
                    ] = expr_pred[i]
                    i += 1
                adata.X = adata.X.tocsr()
                print(
                    "saving the file under the path: ",
                    self.config_init[subcommand]["output_filename"],
                )
                adata.var.drop(columns=["stable_id"], inplace=True)
                adata.write(
                    self.config_init[subcommand]["output_filename"] + "_denoised.h5ad"
                )

    def before_instantiate_classes(self):
        for k, v in self.config.items():
            if "set_float32_matmul_precision" in k:
                if v:
                    torch.set_float32_matmul_precision("medium")
