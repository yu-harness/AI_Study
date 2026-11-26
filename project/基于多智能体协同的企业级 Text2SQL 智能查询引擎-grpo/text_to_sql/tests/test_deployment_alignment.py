import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestDeploymentAlignment(unittest.TestCase):
    def test_runtime_configs_use_documented_coder_temperature_and_sqlite_target(self):
        for name in (
            "config.yaml",
            "config.runtime.yaml",
            "config.docker.yaml",
            "config.k8s.yaml",
        ):
            config = yaml.safe_load((PROJECT_ROOT / name).read_text(encoding="utf-8"))
            with self.subTest(config=name):
                self.assertEqual(config["llm"]["coder"]["temperature"], 0.7)
                self.assertEqual(
                    config["database"]["targets"]["local_sqlite"]["url"],
                    "sqlite:///./data/sandbox.sqlite",
                )

    def test_container_image_includes_sqlite_database(self):
        dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

        self.assertIn("!data/sandbox.sqlite", dockerignore.splitlines())

    def test_kubernetes_exposes_stable_and_ten_percent_canary_ingresses(self):
        stable_documents = list(
            yaml.safe_load_all((PROJECT_ROOT / "k8s" / "text2sql.yaml").read_text(encoding="utf-8"))
        )
        config_map = next(item for item in stable_documents if item.get("kind") == "ConfigMap")
        embedded_config = yaml.safe_load(config_map["data"]["config.yaml"])
        stable_ingress = next(item for item in stable_documents if item.get("kind") == "Ingress")

        self.assertEqual(embedded_config["llm"]["coder"]["temperature"], 0.7)
        self.assertIn("local_sqlite", embedded_config["database"]["targets"])
        self.assertEqual(stable_ingress["spec"]["ingressClassName"], "nginx")

        canary_documents = list(
            yaml.safe_load_all(
                (PROJECT_ROOT / "k8s" / "text2sql-canary.yaml").read_text(encoding="utf-8")
            )
        )
        canary_ingress = next(item for item in canary_documents if item.get("kind") == "Ingress")
        annotations = canary_ingress["metadata"]["annotations"]
        self.assertEqual(annotations["nginx.ingress.kubernetes.io/canary"], "true")
        self.assertEqual(annotations["nginx.ingress.kubernetes.io/canary-weight"], "10")

    def test_rollout_script_keeps_three_models_and_supports_rollback(self):
        script = (PROJECT_ROOT / "scripts" / "rollout-model.ps1").read_text(encoding="utf-8")

        self.assertIn('ValidateSet("Canary", "Promote", "Rollback")', script)
        self.assertIn("Select-Object -First 3", script)
        self.assertIn('deployment/text2sql-api-canary', script)
        self.assertIn('nginx.ingress.kubernetes.io/canary-weight=0', script)


if __name__ == "__main__":
    unittest.main()
