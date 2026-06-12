class SizePredictionEngine:
    
    @staticmethod
    def predict_size(profile, garment):
        """
        Predicts size and returns confidence details based on user body measurements and garment specs.
        
        Args:
            profile (dict): User profile containing height, weight, gender, body_type, etc.
            garment (dict): Garment specs containing category, garment_name, etc.
            
        Returns:
            dict: {
                "recommended_size": "M",
                "confidence": 92,
                "explanation": "..."
            }
        """
        # Return default if profile metrics are missing
        if not profile or not profile.get("height") or not profile.get("weight"):
            return {
                "recommended_size": "M",
                "confidence": 70,
                "explanation": "Complete your body profile questionnaire (height, weight, body type) to unlock accurate size predictions."
            }
            
        try:
            height = float(profile["height"])
            weight = float(profile["weight"])
        except ValueError:
            return {
                "recommended_size": "M",
                "confidence": 65,
                "explanation": "Invalid body profile measurements. Please review your settings."
            }

        gender = (profile.get("gender") or "unisex").lower()
        body_type = (profile.get("body_type") or "average").lower()
        category = (garment.get("category") or "unisex").lower()
        
        # Calculate Body Mass Index (BMI) to determine volume categories
        height_m = height / 100.0
        bmi = weight / (height_m * height_m)
        
        # Determine base size category
        base_size = "M"
        confidence = 90
        
        if gender == "female":
            # Female sizing matrix based on weight and BMI
            if weight < 50 or bmi < 18.5:
                base_size = "XS" if weight < 45 else "S"
            elif 50 <= weight < 62 and 18.5 <= bmi < 23:
                base_size = "S" if weight < 55 else "M"
            elif 62 <= weight < 75 and 23 <= bmi < 27:
                base_size = "M" if weight < 68 else "L"
            elif 75 <= weight < 88 and 27 <= bmi < 32:
                base_size = "L" if weight < 80 else "XL"
            else:
                base_size = "XXL"
        else:
            # Male / Unisex sizing matrix
            if weight < 60 or bmi < 18.5:
                base_size = "S"
            elif 60 <= weight < 74 and 18.5 <= bmi < 23.5:
                base_size = "M"
            elif 74 <= weight < 88 and 23.5 <= bmi < 27.5:
                base_size = "L"
            elif 88 <= weight < 100 and 27.5 <= bmi < 32:
                base_size = "XL"
            else:
                base_size = "XXL"

        # Fit adjustments based on category and body type
        tight_fit_categories = ["blazers", "dresses", "jeans", "ethnic wear"]
        loose_fit_categories = ["t-shirts", "hoodies", "kids wear"]
        
        explanations = []
        
        # Body Type factor adjustments
        if body_type == "athletic":
            if category in tight_fit_categories:
                # Athletic builds need room in shoulders/chest - size up for tight categories
                if base_size == "S": base_size = "M"
                elif base_size == "M": base_size = "L"
                elif base_size == "L": base_size = "XL"
                confidence = 92
                explanations.append("For athletic builds, we recommend sizing up on structured fits to provide comfort around the chest and shoulders.")
            else:
                confidence = 95
                explanations.append("Standard relaxed items fit highly true-to-size on athletic body types.")
                
        elif body_type == "hourglass":
            confidence = 94
            explanations.append("Hourglass silhouettes fit beautifully in tailored waists. Your standard size is highly recommended.")
            
        elif body_type == "pear" or body_type == "triangle":
            if category == "jeans" or category == "dresses":
                # Pear shapes have wider hips - size up for bottoms/dresses
                if base_size == "S": base_size = "M"
                elif base_size == "M": base_size = "L"
                elif base_size == "L": base_size = "XL"
                confidence = 88
                explanations.append("For pear shapes, we recommend sizing up on jeans and fitted dresses to ensure a comfortable drape around the hips.")
            else:
                confidence = 90
                explanations.append("Upper garments match standard specifications perfectly.")
                
        elif body_type in ["round", "oval"]:
            if category in tight_fit_categories:
                # Size up for tight-fitting blazers/jeans
                if base_size == "S": base_size = "M"
                elif base_size == "M": base_size = "L"
                elif base_size == "L": base_size = "XL"
                confidence = 86
                explanations.append("Sizing up ensures an elegant, structured drape without restricting movement.")
            else:
                confidence = 90
                explanations.append("Loose casual shirts and hoodies fit comfortably in your predicted size.")
                
        else:
            # Average/Rectangle body types
            confidence = 92
            explanations.append("Matches clean standard industrial charts for average/symmetrical body ratios.")

        # Default explanation summary
        category_title = category.capitalize()
        height_weight_desc = f"Based on your height ({height} cm) and weight ({weight} kg)"
        
        if not explanations:
            explanation_str = f"{height_weight_desc}, this {category_title} is predicted to fit perfectly in size {base_size}."
        else:
            explanation_str = f"{height_weight_desc}, {explanations[0]} This ensures a secure fit with {confidence}% confidence."
            
        return {
            "recommended_size": base_size,
            "confidence": confidence,
            "explanation": explanation_str
        }
