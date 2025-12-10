# app/services/geoai_pipeline.py

from app.services.geoai_feature_engineer import GeoAIFeatureEngineer
from app.services.geoai_model import GeoAIClassifier

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


class GeoAIPipeline:
    def __init__(self):
        self.engineer = GeoAIFeatureEngineer()
        self.model = GeoAIClassifier()

    # --------------------- Train (내부 test 포함) ---------------------
    def run(self):
        """
        1) train.csv 에 대해 Feature Engineering 실행
        2) RandomForest 학습 + (train 내부) test 성능 출력
        """
        print("🚀 GeoAI FeatureEngineer (축소버전) 활성화\n")
        df_train = self.engineer.run()   # 여기서 train.csv + 공간 피처 붙음
        df_train = df_train.loc[:, ~df_train.columns.duplicated()]  # 추가
        clf = self.model.train(df_train) # 여기서 train/test split + 성능 출력
        self.model.clf = clf

        return df_train

    # ---------------- Feature Importance PNG 저장 ----------------
    def save_feature_importance(self, output_path="feature_importance.png"):
        clf = self.model.clf
        feature_names = self.model.feature_names_

        importances = clf.feature_importances_
        indices = np.argsort(importances)

        plt.figure(figsize=(10, 8))
        plt.title("Feature Importance (Random Forest)", fontsize=16)
        plt.barh(range(len(indices)), importances[indices])
        plt.yticks(
            range(len(indices)),
            [feature_names[i] for i in indices],
            fontsize=9,
        )
        plt.xlabel("Importance", fontsize=12)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"📌 Feature Importance 저장됨 → {output_path}")

    # ---------------- Confusion Matrix PNG 저장 ----------------
    def save_confusion_matrix(self, output_path="confusion_matrix.png"):
        y_true = self.model.last_y_test
        y_pred = self.model.last_y_pred

        if y_true is None or y_pred is None:
            print("⚠️ 아직 train 내부 test 결과가 없습니다.")
            return

        labels = sorted(list(set(y_true)))
        cm = confusion_matrix(y_true, y_pred, labels=labels)

        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=labels,
            yticklabels=labels,
        )
        plt.title("Confusion Matrix (Internal Test Split)", fontsize=16)
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"📌 Confusion Matrix 저장됨 → {output_path}")

    # ---------------- Class별 성능 표 출력 ----------------
    def print_class_performance(self):
        y_true = self.model.last_y_test
        y_pred = self.model.last_y_pred

        if y_true is None or y_pred is None:
            print("⚠️ 아직 train 내부 test 결과가 없습니다.")
            return

        labels = sorted(list(set(y_true)))

        print("\n📊 === Class별 성능 요약 (Internal Test Split 기준) ===")
        print(f"{'클래스':<12} {'Precision':>10} {'Recall':>10} {'F1':>10}")

        for cls in labels:
            p = precision_score(
                y_true, y_pred, labels=[cls], average="macro", zero_division=0
            )
            r = recall_score(
                y_true, y_pred, labels=[cls], average="macro", zero_division=0
            )
            f = f1_score(
                y_true, y_pred, labels=[cls], average="macro", zero_division=0
            )
            print(f"{cls:<12} {p:>10.2f} {r:>10.2f} {f:>10.2f}")


    @staticmethod
    def align_test_columns(df_test, train_features):
        # 1) 공백 제거
        df_test.columns = df_test.columns.str.strip()

        # 2) train에 있는데 test에 없는 컬럼은 0으로 생성
        for col in train_features:
            if col not in df_test.columns:
                df_test[col] = 0

        # 3) test에 있는데 train에 없는 컬럼은 삭제
        cols_to_drop = [
            c for c in df_test.columns
            if c not in train_features and c != "대분류"
        ]
        if cols_to_drop:
            df_test = df_test.drop(columns=cols_to_drop)

        # 4) 순서 강제 정렬
        df_test = df_test[train_features]

        return df_test

    
    # ---------------- (옵션) test_data.csv 별도 평가 ----------------
    def evaluate_on_test(self, test_csv_path: str):
        print(f"📂 test CSV 로드 중 → {test_csv_path}")

        df_test_fe = self.engineer.run_test(test_csv_path)
        df_test_fe = df_test_fe.loc[:, ~df_test_fe.columns.duplicated()]
        print("📊 test feature-engineered shape:", df_test_fe.shape)

        train_features = self.model.feature_names_
        print("🔥 TRAIN FEATURE LIST:", train_features)

        # --- 여기서 test feature를 train과 완전히 동일하게 재구성 ---
        df_test_aligned = pd.DataFrame({
            col: df_test_fe[col].astype(float)
            for col in train_features
        })  

        print("🔥 TEST ALIGNED COLS:", df_test_aligned.columns.tolist())

        preds = self.model.clf.predict(df_test_aligned)
        print("🎯 === TEST 예측 결과 ===")
        print(preds[:20])

        # test CSV 에 '대분류' 있으면 성능도 출력
        if "대분류" in df_test_fe.columns:
            y_true = df_test_fe["대분류"]
            print("\n📊 === TEST 성능 (test_data.csv 기준) ===")
            from sklearn.metrics import classification_report
            print(classification_report(y_true, preds))

        return preds


if __name__ == "__main__":
    pipe = GeoAIPipeline()

    # 1) train.csv 기준으로 학습 + 내부 test 평가
    pipe.run()

    # 2) 그 내부 test 결과 기준으로 PNG/표 뽑기
    #   (생성 경로: app/services/feature_importance.png, confusion_matrix.png)
    pipe.save_feature_importance("feature_importance.png")
    pipe.save_confusion_matrix("confusion_matrix.png")
    pipe.print_class_performance()

    # 3) test_data.csv 별도 평가가 진짜 필요하면, 이 줄을 수동으로 추가해서 사용
    pipe.evaluate_on_test(r"data/test_data.csv")
